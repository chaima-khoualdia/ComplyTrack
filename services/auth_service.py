"""
Authentication service for JWT token management and user verification.
Handles token creation, validation, and password verification.
"""

import os
import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from sqlalchemy.orm import Session
from models.user import User
from dotenv import load_dotenv
from services.notification_service import send_email
from db import get_session

# Load environment variables
load_dotenv()

# Logger setup (ensure logs emit even if root is unset)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = True
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.DEBUG)

# OAuth2 bearer token parser
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login-step2")

# Password hashing context: prefer argon2 (modern, no length limits), support bcrypt for legacy
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto"
)

# JWT configuration from environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-key-change-this-in-production-min-32-chars")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Token expiration: fixed to app lifetime (app startup + 24h)
# On app reload, APP_STARTUP_TIME resets and previously issued tokens become invalid.
APP_STARTUP_TIME = datetime.now(timezone.utc)
TOKEN_EXPIRATION_TIME = APP_STARTUP_TIME + timedelta(hours=24)

# OTP configuration
OTP_EXPIRATION_MINUTES = int(os.getenv("OTP_EXPIRATION_MINUTES", "5"))

# In-memory OTP store: { email: {"otp": str, "expires_at": datetime, "user_id": int, "role": str} }
_otp_store: Dict[str, Dict[str, object]] = {}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a bcrypt hash.
    
    Args:
        plain_password: The plain text password from user input
        hashed_password: The bcrypt hash from database
        
    Returns:
        True if password matches hash, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        # Legacy support for SHA-256 hex hashes that were stored without salt
        if len(hashed_password) == 64 and all(c in "0123456789abcdef" for c in hashed_password.lower()):
            return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
        logger.warning("Unknown password hash format encountered")
        return False


def authenticate_user(email: str, password: str, session: Session) -> Optional[User]:
    """
    Authenticate a user by email and password.
    
    Args:
        email: User's email address
        password: Plain text password from login form
        session: SQLAlchemy database session
        
    Returns:
        User object if authentication successful, None otherwise
    """
    try:
        user = session.query(User).filter(User.email == email).first()
    except Exception:
        logger.exception("DB error while fetching user by email")
        raise
    
    if not user:
        logger.warning("Login failed: user not found for email=%s", email)
        return None
    
    if not verify_password(password, user.password_hash):
        logger.warning("Login failed: password mismatch for email=%s", email)
        return None
    
    return user


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token with the provided data.
    Token expires when the app reloads (max 24 hours from startup).
    
    Args:
        data: Dictionary containing token claims (sub, role, etc)
        expires_delta: Ignored (tokens bound to app lifetime)
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    # Ensure 'sub' (subject) is a string as required by PyJWT
    if 'sub' in to_encode and not isinstance(to_encode['sub'], str):
        to_encode['sub'] = str(to_encode['sub'])
    
    # Set expiration to app startup time + 24 hours (until app reload)
    to_encode.update({"exp": TOKEN_EXPIRATION_TIME})
    
    # Encode JWT token
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Dictionary of decoded token claims if valid, None if invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Token has expired
        return None
    except jwt.InvalidTokenError:
        # Token is invalid (malformed, wrong signature, etc)
        return None


# --- Auth dependencies ---

def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    """Resolve the bearer token into a User, enforcing validity and existence."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise credentials_exception

    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise credentials_exception

    user = session.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user


def require_roles(*allowed_roles: str):
    """Dependency factory to enforce role-based access."""

    allowed = {r.lower() for r in allowed_roles}

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if allowed and current_user.role.lower() not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return dependency


def get_password_hash(password: str) -> str:
    """
    Hash a plain password using argon2.
    Useful for user registration/password reset functionality.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Argon2 hash of the password
    """
    return pwd_context.hash(password)


# --- OTP helpers ---

def generate_otp() -> str:
    """Generate a 6-digit numeric OTP as a zero-padded string."""
    return f"{secrets.randbelow(10**6):06d}"


def create_and_send_otp(user: User) -> bool:
    """Create an OTP for the user, store it with expiration, and send via email."""
    try:
        otp = generate_otp()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRATION_MINUTES)
        email_key = user.email.strip().lower()

        _otp_store[email_key] = {
            "otp": otp,
            "expires_at": expires_at,
            "user_id": user.id,
            "role": user.role,
        }

        subject = "Your Login Verification Code"
        body = (
            f"Hello {user.first_name},\n\n"
            f"Your verification code is: {otp}\n"
            f"This code expires in {OTP_EXPIRATION_MINUTES} minutes.\n\n"
            f"If you did not request this, please ignore this email."
        )

        sent = send_email(user.email, subject, body)
        if not sent:
            logger.error("Failed to send OTP email to %s (check EMAIL_USER/EMAIL_PASS)", user.email)
        else:
            logger.info("OTP sent to %s; expires at %s (key=%s)", user.email, expires_at.isoformat(), email_key)
        return sent
    except Exception:
        logger.exception("Unexpected error while creating/sending OTP for %s", user.email)
        raise


def verify_otp(email: str, otp: str) -> Optional[dict]:
    """Verify the provided OTP for the given email.

    Returns a dict with user_id and role if valid; otherwise None.
    """
    email_key = email.strip().lower()
    otp = otp.strip()
    record = _otp_store.get(email_key)
    if not record:
        logger.warning("OTP verify failed: no record for email=%s", email_key)
        return None

    now = datetime.now(timezone.utc)
    if now > record["expires_at"]:
        logger.warning("OTP expired for email=%s; expires_at=%s", email_key, record["expires_at"].isoformat())
        _otp_store.pop(email_key, None)
        return None

    if record["otp"] != otp:
        logger.warning("OTP mismatch for email=%s", email_key)
        return None

    _otp_store.pop(email_key, None)
    logger.info("OTP verified for email=%s", email_key)
    return {"user_id": record["user_id"], "role": record["role"]}

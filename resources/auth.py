"""
Authentication endpoints for user login and token generation.
Provides JWT-based authentication for the API.
"""

import logging
import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db import get_session
from models.user import User
from schemas import Token, TokenData, LoginRequest, OtpRequest, RegisterRequest, RegisterResponse
from services.auth_service import (
    authenticate_user,
    create_access_token,
    create_and_send_otp,
    verify_otp,
    get_password_hash,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login-step1")
def login_step1(
    body: LoginRequest,
    session: Session = Depends(get_session)
):
    """
    Step 1: Validate credentials, generate OTP, and email it to the user.
    """
    user = authenticate_user(body.email, body.password, session)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sent = create_and_send_otp(user)
    if not sent:
        logger.error("login-step1: failed to send OTP to %s", user.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP email"
        )

    return {"message": "OTP sent to your email"}


@router.post("/login-step2", response_model=Token)
def login_step2(
    body: OtpRequest,
):
    """
    Step 2: Verify OTP and issue JWT token.
    """
    otp_result = verify_otp(body.email, body.otp)
    if not otp_result:
        logger.warning("login-step2: OTP invalid/expired for %s", body.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {
        "sub": otp_result["user_id"],
        "role": otp_result["role"],
    }
    access_token = create_access_token(data=token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/register", response_model=RegisterResponse)
def register(
    body: RegisterRequest,
    session: Session = Depends(get_session),
):
    """
    Public self-registration endpoint - creates user account only.
    Role-specific next steps:
    - owner: redirect to POST /startups to create startup
    - worker: redirect to POST /requests to request startup access
    - investor: proceed to dashboard
    
    Note: Admin accounts cannot be created via public registration.
    """
    role_normalized = body.role.lower()
    role_to_store = "owner" if role_normalized == "startup_owner" else role_normalized

    # Reject admin role from public registration
    if role_to_store == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin accounts cannot be created via public registration"
        )

    # Enforce unique email
    existing = session.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Create user
    hashed_pw = get_password_hash(body.password)
    user = User(
        email=body.email,
        password_hash=hashed_pw,
        role=role_to_store,
        first_name=body.first_name,
        last_name=body.last_name,
        created_at=datetime.utcnow(),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return RegisterResponse(
        message="Registration successful",
        user={
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
    )

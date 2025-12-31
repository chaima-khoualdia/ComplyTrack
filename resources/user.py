from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from passlib.context import CryptContext
from db import get_session
from models import User as UserModel, Startup
from schemas import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])

# Password hashing context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# Helper functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

@router.get("/", response_model=list[UserResponse])
def list_users(session: Session = Depends(get_session)):
    return session.exec(select(UserModel)).all()

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(UserModel, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserResponse)
def create_user(user_create: UserCreate, session: Session = Depends(get_session)):
    # Check if user already exists
    existing = session.exec(select(UserModel).where(UserModel.email == user_create.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create user
    hashed_pw = hash_password(user_create.password)
    new_user = UserModel(
        email=user_create.email,
        password_hash=hashed_pw,
        role=user_create.role,
        first_name=user_create.first_name,
        last_name=user_create.last_name,
        created_at=datetime.utcnow()
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@router.delete("/{user_id}")
def delete_user(user_id: int, session: Session = Depends(get_session)):
    """Delete a user. Prevents deletion if user is a founder of any startup."""
    user = session.get(UserModel, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is founder of any startup
    founder_startups = session.exec(
        select(Startup).where(Startup.founder_id == user_id)
    ).first()
    
    if founder_startups:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete user: Change the owner info for startups before deleting user"
        )
    
    # User is not a founder, proceed with deletion
    session.delete(user)
    session.commit()
    return {"message": "User deleted successfully"}

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from db import get_session
from models import User as UserModel, Startup
from schemas import UserCreate, UserResponse
from services.auth_service import get_password_hash, require_roles

router = APIRouter(prefix="/users", tags=["users"])


# Helper functions
def hash_password(password: str) -> str:
    return get_password_hash(password)

@router.get("/", response_model=list[UserResponse])
def list_users(
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(require_roles("admin")),
):
    return session.exec(select(UserModel)).all()

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(require_roles("admin")),
):
    user = session.get(UserModel, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserResponse)
def create_user(
    user_create: UserCreate,
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(require_roles("admin")),
):
    """Create a new user account (admin-only)."""
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
def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(require_roles("admin")),
):
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

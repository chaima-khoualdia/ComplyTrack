from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from models import User

router = APIRouter(prefix="/users", tags=["users"])

class User:
    @router.get("/{user_id}", response_model=User)
    def get_user(user_id: int, session: Session = Depends(get_session)):
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    @router.post("/", response_model=User)
    def create_user(user: User, session: Session = Depends(get_session)):
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    @router.get("/", response_model=list[User])
    def list_users(session: Session = Depends(get_session)):
        return session.exec(select(User)).all()

    @router.delete("/{user_id}")
    def delete_user(user_id: int, session: Session = Depends(get_session)):
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        session.delete(user)
        session.commit()
        return {"message": "User deleted"}

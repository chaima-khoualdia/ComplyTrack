from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from models import Step, step

router = APIRouter(prefix="/steps", tags=["steps"]) 
class Steps:
    @router.get("/", response_model=list[Step])
    def list_steps(session: Session = Depends(get_session)):
        return session.exec(select(Step)).all()

    @router.get("/by-procedure/{procedure_id}", response_model=list[Step])
    def list_steps_by_procedure(procedure_id: int, session: Session = Depends(get_session)):
        stmt = select(Step).where(Step.procedure_id == procedure_id).order_by(Step.order)
        return session.exec(stmt).all()

    @router.get("/{step_id}", response_model=Step)
    def get_step(step_id: int, session: Session = Depends(get_session)):
        step = session.get(Step, step_id)
        if not step:
            raise HTTPException(status_code=404, detail="Step not found")
        return step
    @router.post("/", response_model=Step)
    def create_step(step: Step, session: Session = Depends(get_session)):
        session.add(step)
        session.commit()
        session.refresh(step)
        return step
    @router.delete("/{step_id}")
    def delete_step(step_id: int, session: Session = Depends(get_session)):
        step = session.get(Step, step_id)
        if not step:
            raise HTTPException(status_code=404, detail="Step not found")
        session.delete(step)
        session.commit()
        return {"message": "Step deleted"}
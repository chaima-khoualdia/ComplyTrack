from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from models import Procedure

router = APIRouter(prefix="/procedures", tags=["procedures"]) 

class Procedures:
    @router.get("/", response_model=list[Procedure])
    def list_procedures(session: Session = Depends(get_session)):
        return session.exec(select(Procedure)).all()

    @router.get("/{procedure_id}", response_model=Procedure)
    def get_procedure(procedure_id: int, session: Session = Depends(get_session)):
        proc = session.get(Procedure, procedure_id)
        if not proc:
            raise HTTPException(status_code=404, detail="Procedure not found")
        return proc

    @router.post("/", response_model=Procedure)
    def create_procedure(procedure: Procedure, session: Session = Depends(get_session)):
        session.add(procedure)
        session.commit()
        session.refresh(procedure)
        return procedure

    @router.delete("/{procedure_id}")
    def delete_procedure(procedure_id: int, session: Session = Depends(get_session)):
        proc = session.get(Procedure, procedure_id)
        if not proc:
            raise HTTPException(status_code=404, detail="Procedure not found")
        session.delete(proc)
        session.commit()
        return {"message": "Procedure deleted"}

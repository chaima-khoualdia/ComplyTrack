import json
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from models import ProcedureProgress

router = APIRouter(prefix="/progress", tags=["progress"])

def load_procedures():
    with open("procedures.json") as f:
        return json.load(f)

@router.post("/", response_model=ProcedureProgress)
def start_procedure(progress: ProcedureProgress, session: Session = Depends(get_session)):
    # Ensure procedure exists in JSON
    procedures = load_procedures()
    if not any(p["id"] == progress.procedure_id for p in procedures):
        raise HTTPException(status_code=404, detail="Procedure not found")
    session.add(progress)
    session.commit()
    session.refresh(progress)
    return progress

@router.patch("/{progress_id}/step")
def complete_step(progress_id: int, session: Session = Depends(get_session)):
    progress = session.get(ProcedureProgress, progress_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")

    procedures = load_procedures()
    procedure = next(p for p in procedures if p["id"] == progress.procedure_id)
    total_steps = len(procedure["steps"])

    if progress.steps_completed >= total_steps:
        raise HTTPException(status_code=400, detail="All steps already completed")

    progress.steps_completed += 1
    session.add(progress)
    session.commit()
    session.refresh(progress)

    return {
        "progress_id": progress.id,
        "startup_id": progress.startup_id,
        "procedure": procedure["name"],
        "steps_completed": progress.steps_completed,
        "total_steps": total_steps,
        "progress_percent": round(progress.steps_completed / total_steps * 100, 2)
    }

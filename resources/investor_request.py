from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from db import get_session
from models import InvestorRequest

router = APIRouter(prefix="/investor-requests", tags=["investor-requests"])

class Request:
    @router.get("/by-startup/{startup_id}", response_model=list[InvestorRequest])
    def list_by_startup(startup_id: int, session: Session = Depends(get_session)):
        stmt = select(InvestorRequest).where(InvestorRequest.startup_id == startup_id)
        return session.exec(stmt).all()
    @router.get("/{request_id}", response_model=InvestorRequest)
    def get_request(request_id: int, session: Session = Depends(get_session)):
        req = session.get(InvestorRequest, request_id)
        if not req:
            raise HTTPException(status_code=404, detail="Investor request not found")
        return req
    @router.post("/", response_model=InvestorRequest)
    def create_request(req: InvestorRequest, session: Session = Depends(get_session)):
        if getattr(req, "request_date", None) is None:
            req.request_date = datetime.utcnow()
        session.add(req)
        session.commit()
        session.refresh(req)
        return req

    @router.delete("/{request_id}")
    def delete_request(request_id: int, session: Session = Depends(get_session)):
        req = session.get(InvestorRequest, request_id)
        if not req:
            raise HTTPException(status_code=404, detail="Investor request not found")
        session.delete(req)
        session.commit()
        return {"message": "Investor request deleted"}

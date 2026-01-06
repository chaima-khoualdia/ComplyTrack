from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from typing import List, Optional, Dict, Any
from db import get_session
from models import InvestorRequest, Startup, User
from schemas import (
    ComplianceSummaryAtRequest,
    StartupComplianceSnapshot,
    InvestorRequestSummary,
    InvestorRequestDetail,
    InvestorDashboardResponse,
)
from services.compliance_service import build_compliance_summary_from_procedures
from services.auth_service import require_roles

router = APIRouter(prefix="/investor-requests", tags=["investor-requests"])

class Request:
    @router.get("/by-startup/{startup_id}", response_model=list[InvestorRequest])
    def list_by_startup(
        startup_id: int,
        session: Session = Depends(get_session),
        current_user=Depends(require_roles("admin", "investor")),
    ):
        """Get all investor requests for a specific startup"""
        stmt = select(InvestorRequest).where(InvestorRequest.startup_id == startup_id)
        return session.exec(stmt).all()
    
    @router.get("/{request_id}", response_model=InvestorRequest)
    def get_request(
        request_id: int,
        session: Session = Depends(get_session),
        current_user=Depends(require_roles("admin", "investor")),
    ):
        """Get a specific investor request by ID"""
        req = session.get(InvestorRequest, request_id)
        if not req:
            raise HTTPException(status_code=404, detail="Investor request not found")
        return req
    
    @router.post("/", response_model=InvestorRequest)
    def create_request(
        req: InvestorRequest,
        session: Session = Depends(get_session),
        current_user=Depends(require_roles("admin", "investor")),
    ):
        """
        Create a new investor request.
        Automatically populates request_date and fetches current badge_status.
        """
        if current_user.role.lower() != "admin" and req.investor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed to create requests for another investor")
        # Verify startup exists
        startup = session.get(Startup, req.startup_id)
        if not startup:
            raise HTTPException(status_code=404, detail="Startup not found")
        
        # Verify investor exists
        investor = session.get(User, req.investor_id)
        if not investor:
            raise HTTPException(status_code=404, detail="Investor not found")
        
        # Auto-populate request_date if not provided
        if getattr(req, "request_date", None) is None:
            req.request_date = datetime.utcnow()
        
        # Fetch current compliance badge status and save at time of request
        try:
            compliance_data = build_compliance_summary_from_procedures(req.startup_id, session)
            req.badge_status_at_request = compliance_data.get("badge_status", "red")
        except Exception as e:
            # If compliance check fails, default to red (safest assumption)
            req.badge_status_at_request = "red"
        
        session.add(req)
        session.commit()
        session.refresh(req)
        return req

    @router.delete("/{request_id}")
    def delete_request(
        request_id: int,
        session: Session = Depends(get_session),
        current_user=Depends(require_roles("admin")),
    ):
        """Delete an investor request"""
        req = session.get(InvestorRequest, request_id)
        if not req:
            raise HTTPException(status_code=404, detail="Investor request not found")
        session.delete(req)
        session.commit()
        return {"message": "Investor request deleted"}
    
    @router.get("/summary/{startup_id}", response_model=InvestorRequestSummary)
    def get_request_summary(
        startup_id: int,
        session: Session = Depends(get_session),
        current_user=Depends(require_roles("admin", "investor")),
    ):
        """
        Get the most recent investor request for a startup with compliance snapshot.
        Returns startup_name, matricule_fiscal, badge_status_at_request, and request_date.
        """
        # Get the most recent request for this startup
        stmt = (select(InvestorRequest)
                .where(InvestorRequest.startup_id == startup_id)
                .order_by(InvestorRequest.request_date.desc())
                .limit(1))
        req = session.exec(stmt).first()
        
        if not req:
            raise HTTPException(status_code=404, detail=f"No investor requests found for startup {startup_id}")
        
        # Get startup details
        startup = session.get(Startup, startup_id)
        if not startup:
            raise HTTPException(status_code=404, detail="Startup not found")
        
        # Build response with startup compliance snapshot
        return InvestorRequestSummary(
            id=req.id,
            investor_id=req.investor_id,
            startup_id=req.startup_id,
            startup=StartupComplianceSnapshot(
                startup_id=startup.id,
                startup_name=startup.name,
                matricule_fiscal=startup.matricule_fiscal,
                legal_form=startup.legal_form,
                location=startup.location,
                badge_status_at_request=req.badge_status_at_request,
                request_date=req.request_date
            ),
            badge_status_at_request=req.badge_status_at_request,
            request_date=req.request_date
        )
    
    @router.get("/by-investor/{investor_id}", response_model=InvestorDashboardResponse)
    def get_investor_requests(
        investor_id: int,
        session: Session = Depends(get_session),
        current_user=Depends(require_roles("admin", "investor")),
    ):
        """
        Get all requests made by a specific investor.
        Returns investor details, all requests, and startup details with badge status at request time.
        """
        if current_user.role.lower() != "admin" and investor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed to view other investors' requests")
        # Verify investor exists
        investor = session.get(User, investor_id)
        if not investor:
            raise HTTPException(status_code=404, detail="Investor not found")
        
        # Get all requests by this investor
        stmt = (select(InvestorRequest)
                .where(InvestorRequest.investor_id == investor_id)
                .order_by(InvestorRequest.request_date.desc()))
        requests = session.exec(stmt).all()
        
        # Build investor-friendly response
        request_details = []
        today = datetime.utcnow().date()
        
        for req in requests:
            startup = session.get(Startup, req.startup_id)
            if startup:
                # Calculate days since request
                request_date_only = req.request_date.date() if hasattr(req.request_date, 'date') else req.request_date
                days_since = (today - request_date_only).days if isinstance(request_date_only, type(today)) else 0
                
                request_details.append(InvestorRequestDetail(
                    id=req.id,
                    investor_id=req.investor_id,
                    investor_name=f"{investor.first_name} {investor.last_name}",
                    startup_id=req.startup_id,
                    startup_name=startup.name,
                    matricule_fiscal=startup.matricule_fiscal,
                    location=startup.location,
                    legal_form=startup.legal_form,
                    badge_status_at_request=req.badge_status_at_request,
                    request_date=req.request_date,
                    days_since_request=days_since
                ))
        
        return InvestorDashboardResponse(
            investor_id=investor_id,
            investor_name=f"{investor.first_name} {investor.last_name}",
            total_requests=len(request_details),
            requests=request_details
        )

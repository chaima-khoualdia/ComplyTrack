from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlmodel import Session, select
from datetime import datetime
import secrets

from models import Request, Startup, User
from db import get_session
from services.auth_service import get_current_user, require_roles

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post("/", response_model=Dict[str, Any])
def create_request(
    startup_id: int = Body(..., embed=True),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("worker")),
):
    """Worker creates a request to join a startup"""
    # Verify startup exists
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Startup not found")
    
    # Check for existing request
    existing_request = session.exec(
        select(Request).where(
            Request.worker_user_id == current_user.id,
            Request.startup_id == startup_id,
            Request.status.in_(["pending", "approved", "active"])
        )
    ).first()
    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You already have a {existing_request.status} request for this startup"
        )
    
    # Create request
    request = Request(
        worker_user_id=current_user.id,
        startup_id=startup_id,
        owner_user_id=startup.founder_id,
        status="pending",
        created_at=datetime.utcnow(),
    )
    session.add(request)
    session.commit()
    session.refresh(request)
    
    return {
        "id": request.id,
        "worker_user_id": request.worker_user_id,
        "startup_id": request.startup_id,
        "owner_user_id": request.owner_user_id,
        "status": request.status,
        "message": "Request created successfully. Waiting for owner approval.",
    }


@router.get("/startup/{startup_id}", response_model=list[Dict[str, Any]])
def get_startup_requests(
    startup_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin", "owner")),
):
    """Get all pending requests for a startup (owner access required)"""
    # Get the startup
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Startup not found")
    
    # Verify ownership (admin can see all, owner can see only their startup)
    if current_user.role != "admin" and startup.founder_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view requests for your own startup"
        )
    
    # Query requests
    statement = select(Request).where(
        Request.startup_id == startup_id,
        Request.status == "pending"
    )
    requests = session.exec(statement).all()
    
    # Return formatted data
    return [
        {
            "id": req.id,
            "worker_user_id": req.worker_user_id,
            "worker_email": req.worker.email if req.worker else None,
            "worker_name": f"{req.worker.first_name} {req.worker.last_name}" if req.worker else None,
            "startup_id": req.startup_id,
            "status": req.status,
            "created_at": req.created_at.isoformat() if req.created_at else None,
        }
        for req in requests
    ]


@router.patch("/{request_id}/approve", response_model=Dict[str, Any])
def approve_request(
    request_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin", "owner")),
):
    """Approve a worker's request to join a startup (generates invitation code)"""
    # Get the request
    req = session.get(Request, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    
    # Verify ownership
    if current_user.role != "admin" and req.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only approve requests for your own startup"
        )
    
    # Check status
    if req.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve request with status: {req.status}"
        )
    
    # Generate invitation code and update status
    req.invitation_code = secrets.token_urlsafe(16)
    req.status = "approved"
    req.updated_at = datetime.utcnow()
    
    session.add(req)
    session.commit()
    session.refresh(req)
    
    return {
        "id": req.id,
        "status": req.status,
        "invitation_code": req.invitation_code,
        "message": "Request approved successfully. Share the invitation code with the worker.",
    }


@router.patch("/{request_id}/reject", response_model=Dict[str, Any])
def reject_request(
    request_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin", "owner")),
):
    """Reject a worker's request to join a startup"""
    # Get the request
    req = session.get(Request, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    
    # Verify ownership
    if current_user.role != "admin" and req.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only reject requests for your own startup"
        )
    
    # Check status
    if req.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject request with status: {req.status}"
        )
    
    # Update status
    req.status = "rejected"
    req.updated_at = datetime.utcnow()
    
    session.add(req)
    session.commit()
    session.refresh(req)
    
    return {
        "id": req.id,
        "status": req.status,
        "message": "Request rejected successfully",
    }


@router.post("/{request_id}/confirm", response_model=Dict[str, Any])
def confirm_request(
    request_id: int,
    invitation_code: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("worker")),
):
    """Worker confirms their request using invitation code (activates the request)"""
    # Get the request
    req = session.get(Request, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    
    # Verify worker ownership
    if req.worker_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only confirm your own requests"
        )
    
    # Check status
    if req.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot confirm request with status: {req.status}. Request must be approved first."
        )
    
    # Validate invitation code
    if req.invitation_code != invitation_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invitation code"
        )
    
    # Activate the request
    req.status = "active"
    req.updated_at = datetime.utcnow()
    
    session.add(req)
    session.commit()
    session.refresh(req)
    
    return {
        "id": req.id,
        "status": req.status,
        "startup_id": req.startup_id,
        "message": "Request confirmed successfully. You are now active in the startup.",
    }

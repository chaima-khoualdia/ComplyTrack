from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional

# ====== User Schemas ======
class UserCreate(BaseModel):
    email: str
    password: str
    role: str
    first_name: str
    last_name: str

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    first_name: str
    last_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# ====== Startup Schemas ======
class StartupCreate(BaseModel):
    founder_id: int
    name: str
    matricule_fiscal: str
    rne_number: str
    legal_form: str        # e.g. "SARL", "SA"
    field: str             # e.g. "tech", "healthcare", "finance"
    sector: str            # e.g. "private", "public", "ngo"
    size: str              # e.g. "small", "medium", "large"
    location: str          # e.g. "Tunis", "Sfax", "Free Zone"

class StartupResponse(BaseModel):
    id: int
    founder_id: int
    name: str
    matricule_fiscal: str
    rne_number: str
    legal_form: str
    field: str
    sector: str
    size: str
    location: str
    badge_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class StartupUpdate(BaseModel):
    name: Optional[str] = None
    matricule_fiscal: Optional[str] = None
    rne_number: Optional[str] = None
    legal_form: Optional[str] = None
    field: Optional[str] = None
    sector: Optional[str] = None
    size: Optional[str] = None
    location: Optional[str] = None
    badge_status: Optional[str] = None

class StartupCreatedResponse(BaseModel):
    """Response for startup creation with auto-assigned procedures."""
    # Startup fields
    id: int
    founder_id: int
    name: str
    matricule_fiscal: str
    rne_number: str
    legal_form: str
    field: str
    sector: str
    size: str
    location: str
    badge_status: str
    created_at: datetime
    
    # Auto-assigned procedures (one per procedure)
    procedures: list[dict]
    
    # Compliance status (one per domain)
    compliance_status: list[dict]
    
    class Config:
        from_attributes = True

# ====== Source Schemas ======
class SourceCreate(BaseModel):
    title: str
    url: str
    description: Optional[str] = None
    type: str  # "law", "portal", "guide"
    country: str = "Tunisia"
    language: str = "fr"  # "fr", "ar", "en"
    last_verified: Optional[datetime] = None

class SourceResponse(BaseModel):
    id: int
    title: str
    url: str
    description: Optional[str] = None
    type: str
    country: str
    language: str
    last_verified: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ====== Compliance Status Schemas ======
class ComplianceStatusCreate(BaseModel):
    startup_id: int
    procedure_id: Optional[int] = None
    domain: str
    status: str
    due_date: datetime

class ComplianceStatusUpdate(BaseModel):
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class ComplianceStatusResponse(BaseModel):
    id: int
    startup_id: int
    procedure_id: Optional[int] = None
    domain: str
    status: str
    due_date: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ComplianceStatusDetailedResponse(BaseModel):
    """Compliance status with procedure details grouped by domain."""
    id: int
    startup_id: int
    procedure_id: int
    procedure_name: str
    domain: str
    status: str
    due_date: datetime
    completed_at: Optional[datetime] = None

# ====== Reminder Schemas ======
class ReminderCreate(BaseModel):
    startup_id: int
    reminder_date: datetime
    message: str
    status: str = "pending"

class ReminderResponse(BaseModel):
    id: int
    startup_id: int
    reminder_date: datetime
    message: str
    status: str
    
    class Config:
        from_attributes = True

# ====== Investor Request Schemas ======
class InvestorRequestCreate(BaseModel):
    investor_id: int
    startup_id: int
    badge_status_at_request: str

class InvestorRequestResponse(BaseModel):
    id: int
    investor_id: int
    startup_id: int
    request_date: datetime
    badge_status_at_request: str
    
    class Config:
        from_attributes = True

# ====== Public Badge Response ======
class ComplianceBadgeResponse(BaseModel):
    startup_name: str
    matricule_fiscal: str
    badge_status: str
    summary: dict

# ====== Procedure Schemas ======
class ProcedureCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProcedureResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ====== Startup Procedure Schemas ======
class StartupProcedureAssign(BaseModel):
    """Assign one or more procedures to a startup."""
    procedure_ids: list[int]

class StartupProcedureResponse(BaseModel):
    """Response for a startup procedure (one record per procedure, not per step)."""
    id: int
    startup_id: int
    procedure_id: int
    procedure_name: str
    domain: str
    status: str  # pending, in_progress, completed, overdue
    due_date: date
    assigned_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ProcedureStatusUpdate(BaseModel):
    """
    Update procedure status and/or step completion.
    
    Can be used in two ways:
    1. Update procedure status only: {"status": "in_progress"}
    2. Update step completion: {"step_id": 301, "completed": true}
    3. Both: {"status": "in_progress", "step_id": 301, "completed": true}
    """
    status: str = None  # pending, in_progress, completed, overdue
    step_id: int = None  # Optional: ID of step to toggle completion
    completed: bool = None  # Optional: whether step is completed (used if step_id provided)

class StartupProcedureWithDetails(BaseModel):
    """Detailed response including procedure info and all steps from procedures.json."""
    id: int
    startup_id: int
    procedure_id: int
    procedure_name: str
    procedure_description: Optional[str] = None
    completed_step_ids: list[int]
    total_steps: int
    completed_steps: int
    progress_percent: float
    assigned_at: datetime
    steps: list[dict]  # Steps loaded from procedures.json with id, name, description, order, is_required
    sources: list[dict] = []  # Enriched sources with title, url, description
    
    class Config:
        from_attributes = True

class StepToggle(BaseModel):
    """Toggle a step's completion status."""
    completed: bool

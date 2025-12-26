from pydantic import BaseModel
from datetime import datetime

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
    sector: str

class StartupResponse(BaseModel):
    id: int
    founder_id: int
    name: str
    matricule_fiscal: str
    rne_number: str
    sector: str
    badge_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# ====== Source Schemas ======
class SourceCreate(BaseModel):
    step_id: int
    name: str
    url: str

class SourceResponse(BaseModel):
    id: int
    step_id: int
    name: str
    url: str
    
    class Config:
        from_attributes = True

# ====== Compliance Status Schemas ======
class ComplianceStatusCreate(BaseModel):
    startup_id: int
    status: str
    due_date: datetime

class ComplianceStatusUpdate(BaseModel):
    status: str = None
    due_date: datetime = None
    completed_at: datetime = None

class ComplianceStatusResponse(BaseModel):
    id: int
    startup_id: int
    status: str
    due_date: datetime
    completed_at: datetime = None
    
    class Config:
        from_attributes = True

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
    description: str = None

class ProcedureResponse(BaseModel):
    id: int
    name: str
    description: str = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ====== Step Schemas ======
class StepCreate(BaseModel):
    procedure_id: int
    name: str
    description: str = None
    order: int
    is_required: bool = True

class StepResponse(BaseModel):
    id: int
    procedure_id: int
    name: str
    description: str = None
    order: int
    is_required: bool
    
    class Config:
        from_attributes = True

# ====== Startup Procedure Schemas ======
class StartupProcedureAssign(BaseModel):
    """Assign one or more procedures to a startup."""
    procedure_ids: list[int]

class StartupProcedureResponse(BaseModel):
    """Basic response for startup procedure assignment with progress."""
    id: int
    startup_id: int
    procedure_id: int
    completed_step_ids: list[int]
    progress_percent: float
    assigned_at: datetime
    
    class Config:
        from_attributes = True

class StartupProcedureWithDetails(BaseModel):
    """Detailed response including procedure info and all steps."""
    id: int
    startup_id: int
    procedure_id: int
    procedure_name: str
    procedure_description: str = None
    completed_step_ids: list[int]
    total_steps: int
    completed_steps: int
    progress_percent: float
    assigned_at: datetime
    steps: list[StepResponse]
    
    class Config:
        from_attributes = True

class StepToggle(BaseModel):
    """Toggle a step's completion status."""
    step_id: int
    completed: bool
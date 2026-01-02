"""
Services Package
Centralized service layer for business logic.
Imports and exposes all service functions for easy use in routers.
"""

# Procedures Service (consolidated: load_procedures, get_procedure_by_id, get_applicable_procedures, get_matching_procedures)
from services.procedures_service import (
    load_procedures,
    get_procedure_by_id,
    get_applicable_procedures,
    get_matching_procedures
)

# Progress Tracking
from services.progress_service import (
    calculate_progress,
    toggle_step_completion
)

# Assignment Service
from services.assignment_service import (
    assign_procedures_to_startup,
    delete_startup_procedure,
    initialize_startup_procedures
)

# Listing Service
from services.listing_service import (
    list_startup_procedures
)

# Compliance Service
from services.compliance_service import (
    compute_badge,
    summarize_statuses,
    sync_compliance_status_from_procedures
)

__all__ = [
    # Procedures Service
    "load_procedures",
    "get_procedure_by_id",
    "get_applicable_procedures",
    "get_matching_procedures",
    
    # Progress Service
    "calculate_progress",
    "toggle_step_completion",
    
    # Assignment Service
    "assign_procedures_to_startup",
    "delete_startup_procedure",
    "initialize_startup_procedures",
    
    # Listing Service
    "list_startup_procedures",
    
    # Compliance Service
    "compute_badge",
    "summarize_statuses",
    "sync_compliance_status_from_procedures",
]

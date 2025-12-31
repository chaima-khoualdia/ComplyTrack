"""
Services Package
Centralized service layer for business logic.
Imports and exposes all service functions for easy use in routers.
"""

# Procedure Loading
from services.procedure_loader import (
    load_procedures,
    get_procedure_by_id
)

# Progress Tracking
from services.progress_service import (
    calculate_progress,
    toggle_step_completion
)

# Assignment Service
from services.assignment_service import (
    assign_procedures_to_startup,
    delete_startup_procedure
)

# Listing Service
from services.listing_service import (
    list_startup_procedures
)

# Procedure Matching Service
from services.procedure_matching import (
    get_matching_procedures,
    auto_assign_procedures
)

__all__ = [
    # Procedure Loader
    "load_procedures",
    "get_procedure_by_id",
    
    # Progress Service
    "calculate_progress",
    "toggle_step_completion",
    
    # Assignment Service
    "assign_procedures_to_startup",
    "delete_startup_procedure",
    
    # Listing Service
    "list_startup_procedures",
    
    # Procedure Matching Service
    "get_matching_procedures",
    "auto_assign_procedures",
]

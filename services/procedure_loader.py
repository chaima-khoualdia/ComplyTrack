"""
Procedure Loader Service
Handles loading procedures from JSON and retrieving procedure details by ID.
"""

import json
from typing import Optional


def load_procedures() -> list:
    """
    Load all procedures from procedures.json.
    
    Returns:
        List of procedure dictionaries from JSON
    """
    try:
        with open("procedures.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def get_procedure_by_id(procedure_id: int, procedures: list = None) -> Optional[dict]:
    """
    Get a procedure by ID from procedures.json.
    
    Args:
        procedure_id: ID of the procedure
        procedures: Optional pre-loaded procedures list. If None, will load from JSON.
    
    Returns:
        Procedure dictionary or None if not found
    """
    if procedures is None:
        procedures = load_procedures()
    
    return next((p for p in procedures if p["id"] == procedure_id), None)

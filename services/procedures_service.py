"""
Procedures Service
Handles loading, flattening, and filtering procedures from procedures.json
"""

import json
import os
from pathlib import Path
from datetime import date, timedelta
from typing import List, Dict, Any


# Global cache for flattened procedures
_procedures_cache = None


def load_procedures() -> List[Dict[str, Any]]:
    """
    Load procedures.json and flatten all procedures from all domains.
    Each procedure gets a "domain" field added.
    Results are cached for performance.
    
    Returns:
        List of procedure dictionaries with domain field added
    """
    global _procedures_cache
    
    if _procedures_cache is not None:
        return _procedures_cache
    
    try:
        # Resolve procedures.json relative to the repository root (parent of services/)
        repo_root = Path(__file__).resolve().parent.parent
        procedures_path = repo_root / "procedures.json"
        if not procedures_path.exists():
            # Fallback: try current working directory
            procedures_path = Path(os.getcwd()) / "procedures.json"

        with open(procedures_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        flattened = []
        procedures_by_domain = data.get("procedures", {})
        
        # Iterate through each domain (tax_compliance, legal_registration, etc.)
        for domain, procedures_list in procedures_by_domain.items():
            for procedure in procedures_list:
                # Add domain field to each procedure
                procedure_with_domain = {**procedure, "domain": domain}
                flattened.append(procedure_with_domain)
        
        _procedures_cache = flattened
        return flattened
    
    except Exception as e:
        print(f"Error loading procedures.json from {procedures_path}: {e}")
        return []


def get_applicable_procedures(
    legal_form: str,
    industry: str,
    size: str,
    country: str = "TN",
    location: str = None
) -> List[Dict[str, Any]]:
    """
    Filter flattened procedures by startup attributes.
    
    Args:
        legal_form: Legal form (e.g., "SARL", "SA")
        industry: Industry (e.g., "tech", "finance", "healthcare")
        size: Company size (e.g., "small", "medium", "large")
        country: Country code (default: "TN" for Tunisia)
        location: Location (e.g., "Free Zone")
    
    Returns:
        List of applicable procedures
    """
    all_procedures = load_procedures()
    applicable = []
    
    for proc in all_procedures:
        # Check legal_form match
        if legal_form not in proc.get("legal_forms", []) and "all" not in proc.get("legal_forms", []):
            continue
        
        # Check industry match
        if industry not in proc.get("industries", []) and "all" not in proc.get("industries", []):
            continue
        
        # Check size match
        if size not in proc.get("sizes", []):
            continue
        
        # Check country match
        if country not in proc.get("countries", []):
            continue
        
        # Check location match (if specified in procedure)
        if "locations" in proc and location:
            if location not in proc["locations"]:
                continue
        elif "locations" in proc and not location:
            # Procedure requires location, but startup has none
            continue
        
        applicable.append(proc)
    
    return applicable


def get_procedure_by_id(procedure_id: int, procedures: list = None) -> Dict[str, Any]:
    """
    Get a specific procedure by ID.
    
    Args:
        procedure_id: ID of the procedure
        procedures: Optional pre-loaded procedures list. If None, will load from JSON.
    
    Returns:
        Procedure dictionary or None if not found
    """
    if procedures is None:
        procedures = load_procedures()
    
    return next((p for p in procedures if p.get("id") == procedure_id), None)


def get_matching_procedures(
    legal_form: str,
    field: str,
    size: str,
    location: str = None
) -> List[int]:
    """
    Get procedure IDs that match a startup's attributes (for auto-assignment).
    Matches on legal_form, industry, size, and optionally location.
    
    Args:
        legal_form: Legal form (SARL, SA, etc.)
        field: Industry (tech, healthcare, finance, etc.)
        size: Size (small, medium, large)
        location: Location (optional, for free zone matching)
    
    Returns:
        List of procedure IDs that match the startup attributes
    """
    procedures = get_applicable_procedures(
        legal_form=legal_form,
        industry=field,
        size=size,
        location=location
    )
    return [proc["id"] for proc in procedures]


def get_all_procedures() -> List[Dict[str, Any]]:
    """Get all loaded and flattened procedures."""
    return load_procedures()

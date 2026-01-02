"""
Listing Service
Handles listing procedures assigned to a startup with their steps and progress.
"""

import json
from sqlmodel import Session, select
from models import Startup, StartupProcedure, Source
from services.procedures_service import load_procedures, get_procedure_by_id


def enrich_procedure_response(
    startup_procedure: StartupProcedure,
    procedure_def: dict,
    procedures: list[dict],
    source_map: dict
) -> dict:
    """
    Build an enriched procedure response including steps, sources, and progress.
    
    Args:
        startup_procedure: StartupProcedure database record
        procedure_def: Procedure definition from procedures.json
        procedures: All procedures from procedures.json (for reference)
        source_map: Dict mapping source_id to Source model objects
        
    Returns:
        Dictionary with enriched procedure data including steps and progress
    """
    steps_list = procedure_def.get("steps", [])
    procedure_source_ids = procedure_def.get("source_ids", [])
    sources = [
        {
            "id": sid,
            "title": source_map[sid].title,
            "url": source_map[sid].url,
            "description": source_map[sid].description,
        }
        for sid in procedure_source_ids
        if sid in source_map
    ]
    
    # Parse completed_step_ids (stored as JSON string)
    try:
        completed_step_ids = json.loads(startup_procedure.completed_step_ids or "[]")
    except (json.JSONDecodeError, TypeError):
        completed_step_ids = []
    
    # Calculate progress based on actual step completion, not just status
    total_steps = len(steps_list)
    completed_count = len(completed_step_ids)
    
    if startup_procedure.status == "completed":
        # Completed procedures are always 100%
        progress_percent = 100.0
    elif total_steps > 0:
        # Calculate progress based on actual step completion for all other statuses
        progress_percent = (completed_count / total_steps) * 100.0
    else:
        # No steps defined, default to 0%
        progress_percent = 0.0
    
    return {
        "id": startup_procedure.id,
        "startup_id": startup_procedure.startup_id,
        "procedure_id": startup_procedure.procedure_id,
        "procedure_name": startup_procedure.procedure_name,
        "domain": startup_procedure.domain,
        "status": startup_procedure.status,
        "due_date": startup_procedure.due_date,
        "assigned_at": startup_procedure.assigned_at,
        "completed_at": startup_procedure.completed_at,
        "procedure_description": procedure_def.get("description", ""),
        "completed_step_ids": completed_step_ids,
        "total_steps": total_steps,
        "completed_steps": completed_count,
        "progress_percent": progress_percent,
        "sources": sources,
        "steps": [
            {
                "id": s.get("id"),
                "procedure_id": startup_procedure.procedure_id,
                "name": s.get("name", ""),
                "description": s.get("description", ""),
                "order": s.get("order", 0),
                "is_required": s.get("is_required", True),
            }
            for s in steps_list
        ]
    }


def list_startup_procedures(
    startup_id: int,
    session: Session
) -> list:
    """
    List all procedures assigned to a startup with their steps and progress.
    Steps are loaded from procedures.json, not the database.
    
    Returns enriched procedure data including:
    - procedure_name, domain, status, due_date, assigned_at, completed_at from StartupProcedure
    - steps array from procedures.json
    - completed_step_ids (empty array - step tracking removed in refactoring)
    - progress_percent based on procedure status
    - sources enriched with title, url, description
    
    Args:
        startup_id: ID of the startup
        session: Database session
    
    Returns:
        List of dictionaries with procedure details, steps, and progress
    
    Raises:
        ValueError: If startup not found
    """
    # Verify startup exists
    startup = session.get(Startup, startup_id)
    if not startup:
        raise ValueError(f"Startup {startup_id} not found")
    
    procedures = load_procedures()
    
    # Get all startup procedures from database
    stmt = select(StartupProcedure).where(StartupProcedure.startup_id == startup_id)
    startup_procedures = session.exec(stmt).all()

    # Collect all source_ids referenced by assigned procedures
    source_ids: set[int] = set()
    for sp in startup_procedures:
        procedure = get_procedure_by_id(sp.procedure_id, procedures)
        if not procedure:
            continue
        source_ids.update(procedure.get("source_ids", []))

    source_map = {}
    if source_ids:
        db_sources = session.exec(select(Source).where(Source.id.in_(source_ids))).all()
        source_map = {s.id: s for s in db_sources}
    
    results = []
    for sp in startup_procedures:
        # Get procedure details from JSON
        procedure = get_procedure_by_id(sp.procedure_id, procedures)
        if not procedure:
            continue
        
        # Build enriched response
        enriched = enrich_procedure_response(sp, procedure, procedures, source_map)
        results.append(enriched)
    
    return results


def get_procedure_response(
    startup_procedure: StartupProcedure,
    session: Session
) -> dict:
    """
    Get a single procedure with enriched response including steps and progress.
    
    Args:
        startup_procedure: StartupProcedure database record
        session: Database session
        
    Returns:
        Dictionary with enriched procedure data including steps and progress
    """
    procedures = load_procedures()
    procedure = get_procedure_by_id(startup_procedure.procedure_id, procedures)
    
    if not procedure:
        raise ValueError(f"Procedure {startup_procedure.procedure_id} not found in procedures.json")
    
    # Collect source_ids for this procedure
    source_ids = procedure.get("source_ids", [])
    source_map = {}
    if source_ids:
        db_sources = session.exec(select(Source).where(Source.id.in_(source_ids))).all()
        source_map = {s.id: s for s in db_sources}
    
    return enrich_procedure_response(startup_procedure, procedure, procedures, source_map)


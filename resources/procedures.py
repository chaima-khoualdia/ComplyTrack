from fastapi import APIRouter, HTTPException
from services.procedures_service import load_procedures, get_procedure_by_id


router = APIRouter(prefix="/procedures", tags=["procedures"])


@router.get("/{procedure_id}/steps", response_model=list[dict])
def get_procedure_steps(procedure_id: int):
    """Get steps for a procedure from procedures.json."""
    try:
        procedures = load_procedures()
        procedure = get_procedure_by_id(procedure_id, procedures)
        
        if not procedure:
            raise HTTPException(
                status_code=404,
                detail=f"Procedure {procedure_id} not found"
            )
        
        steps = procedure.get("steps", [])
        return [
            {
                "id": s.get("id"),
                "procedure_id": procedure_id,
                "name": s.get("name", ""),
                "description": s.get("description", ""),
                "order": s.get("order", 0),
                "is_required": s.get("is_required", True),
            }
            for s in steps
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

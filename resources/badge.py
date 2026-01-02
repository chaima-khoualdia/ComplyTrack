"""
Badge Router (DEPRECATED)

This router has been merged into resources/compliance_status.py.
The GET /compliance/badge/{identifier} endpoint replaces /public/compliance-badge/{identifier}.

Keep this file for backward compatibility if needed, but all functionality
is now in the compliance_status router.
"""

from fastapi import APIRouter
from sqlmodel import Session
from db import get_session

router = APIRouter(prefix="/public", tags=["public"])

# All badge endpoints moved to /compliance/badge/{identifier}
# See resources/compliance_status.py for the implementation

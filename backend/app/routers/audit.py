from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import AuditLog
from app.schemas import AuditLogOut

router = APIRouter(prefix="/api/audit", tags=["Audit Trail"])

@router.get("", response_model=List[AuditLogOut])
def get_audit_logs(
    policy_override: Optional[bool] = Query(None, description="Filter for policy overrides"),
    simulation_status: Optional[str] = Query(None, description="Filter by simulation status (RECOVERED, FAILED)"),
    approved_action: Optional[str] = Query(None, description="Filter by approved action"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if policy_override is not None:
        query = query.filter(AuditLog.policy_override == policy_override)
    if simulation_status:
        query = query.filter(AuditLog.simulation_status == simulation_status)
    if approved_action:
        query = query.filter(AuditLog.policy_action_approved == approved_action)
    
    return query.order_by(AuditLog.id.desc()).limit(limit).all()

@router.get("/{audit_id}", response_model=AuditLogOut)
def get_audit_entry(audit_id: int, db: Session = Depends(get_db)):
    entry = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Audit log record not found")
    return entry

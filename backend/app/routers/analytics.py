from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import SystemOverview
from app.services.orchestrator import RecoveryOrchestrator

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/overview", response_model=SystemOverview)
def get_system_overview(db: Session = Depends(get_db)):
    """Provides high-level dashboard metrics: revenue at risk, recovered revenue, distributions."""
    return RecoveryOrchestrator.get_system_overview(db)

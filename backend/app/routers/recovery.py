from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.database import get_db
from app.models import PaymentRecord
from app.schemas import RecoveryPipelineResponse, ComparisonSummary, MultiSeedEvaluationResult
from app.services.orchestrator import RecoveryOrchestrator

router = APIRouter(prefix="/api/recovery", tags=["Recovery Pipeline"])

@router.post("/diagnose/{payment_id}", response_model=RecoveryPipelineResponse)
def diagnose_and_recover_single(
    payment_id: int, 
    event_id: Optional[str] = Query(None, description="Unique idempotency event ID to prevent duplicate executions"),
    db: Session = Depends(get_db)
):
    """
    Executes the full recovery pipeline for a single payment with Idempotency Protection:
    Event ID check -> LLM Diagnosis -> Deterministic Policy Engine -> Simulated Recovery -> Audit Log.
    """
    payment = db.query(PaymentRecord).filter(PaymentRecord.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    
    return RecoveryOrchestrator.process_single_payment(payment, db, event_id=event_id)

@router.post("/batch")
def run_batch_ai_recovery(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Runs the RecoverAI workflow across all 100 records."""
    return RecoveryOrchestrator.run_batch_ai_recovery(db)

@router.post("/baseline")
def run_baseline_simulation(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Runs Baseline 1: Naive Blind 3x Retry across all 100 records."""
    return RecoveryOrchestrator.run_baseline_simulation(db)

@router.post("/rule-baseline")
def run_rule_based_simulation(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Runs Baseline 2: Simple Static Rule-Based Recovery across all 100 records."""
    return RecoveryOrchestrator.run_rule_based_simulation(db)

@router.get("/comparison", response_model=ComparisonSummary)
def get_strategy_comparison(db: Session = Depends(get_db)):
    """Returns measured 3-way comparative analytics: Blind Retry vs Rule-Based vs RecoverAI."""
    return RecoveryOrchestrator.get_comparison_summary(db)

@router.get("/multi-seed-evaluation", response_model=MultiSeedEvaluationResult)
def get_multi_seed_evaluation(
    seed_start: int = Query(1, ge=1, le=100),
    seed_end: int = Query(20, ge=1, le=100)
):
    """Executes multi-seed evaluation across seeds to prove statistical significance."""
    return RecoveryOrchestrator.run_multi_seed_evaluation(seed_start=seed_start, seed_end=seed_end, count_per_seed=100)

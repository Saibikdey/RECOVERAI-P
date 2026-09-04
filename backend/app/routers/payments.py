from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import PaymentRecord, AuditLog, ProcessedEvent
from app.schemas import PaymentRecordOut
from app.generator import generate_synthetic_payments

router = APIRouter(prefix="/api/payments", tags=["Payments"])

@router.get("", response_model=List[PaymentRecordOut])
def get_payments(
    status: Optional[str] = Query(None, description="Filter by status (FAILED, RECOVERED, etc.)"),
    error_code: Optional[str] = Query(None, description="Filter by error code"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    customer_tier: Optional[str] = Query(None, description="Filter by customer tier"),
    db: Session = Depends(get_db)
):
    query = db.query(PaymentRecord)
    if status:
        query = query.filter(PaymentRecord.status == status)
    if error_code:
        query = query.filter(PaymentRecord.error_code == error_code)
    if risk_level:
        query = query.filter(PaymentRecord.risk_level == risk_level)
    if customer_tier:
        query = query.filter(PaymentRecord.customer_tier == customer_tier)
    
    return query.order_by(PaymentRecord.id.asc()).all()

@router.get("/{payment_id}", response_model=PaymentRecordOut)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(PaymentRecord).filter(PaymentRecord.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    return payment

@router.post("/reset")
def reset_synthetic_dataset(db: Session = Depends(get_db)):
    """Wipes existing payments, audit logs, & processed idempotency events, and creates a fresh batch of 100 synthetic records."""
    db.query(ProcessedEvent).delete()
    db.query(AuditLog).delete()
    db.query(PaymentRecord).delete()
    db.commit()

    records = generate_synthetic_payments(count=100, seed=42)
    db.add_all(records)
    db.commit()

    return {
        "message": "Successfully generated 100 fresh synthetic failed-payment records",
        "count": len(records),
        "total_revenue_at_risk": sum(r.amount for r in records)
    }

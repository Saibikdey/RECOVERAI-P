from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from datetime import datetime, timezone
from app.database import Base

class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(64), unique=True, index=True, nullable=False)
    customer_id = Column(String(64), index=True, nullable=False)
    customer_name = Column(String(128), nullable=False)
    customer_tier = Column(String(32), default="STANDARD") # STANDARD, VIP, ENTERPRISE
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    payment_method = Column(String(64), nullable=False) # UPI, CREDIT_CARD, DEBIT_CARD, NETBANKING, NACH_MANDATE
    
    error_code = Column(String(64), nullable=False) # INSUFFICIENT_FUNDS, CARD_EXPIRED, BANK_SERVER_DOWN, NETWORK_TIMEOUT, AUTHENTICATION_FAILED_3DS, LIMIT_EXCEEDED, SUSPECTED_FRAUD, DO_NOT_HONOR
    error_message = Column(String(256), nullable=False)
    
    status = Column(String(32), default="FAILED", index=True) # FAILED, RECOVERED, PERMANENTLY_FAILED, IN_PROGRESS
    retry_count = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    risk_score = Column(Float, default=0.5) # 0.0 to 1.0
    risk_level = Column(String(32), default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    
    # 1. RecoverAI Execution Results
    recovery_action_taken = Column(String(32), nullable=True) # RETRY, ALTERNATE_PAYMENT, REMINDER, ESCALATE, NO_ACTION
    recovered_amount = Column(Float, default=0.0)             # Gross recovered
    intervention_cost = Column(Float, default=0.0)            # Synthetic cost incurred
    net_recovered_amount = Column(Float, default=0.0)         # Net = Gross - Cost
    
    # 2. Baseline 1: Naive Blind 3x Retry Simulation Results
    baseline_status = Column(String(32), nullable=True) # RECOVERED, PERMANENTLY_FAILED
    baseline_retries = Column(Integer, default=0)
    baseline_recovered_amount = Column(Float, default=0.0)
    baseline_intervention_cost = Column(Float, default=0.0)
    baseline_net_recovered_amount = Column(Float, default=0.0)

    # 3. Baseline 2: Simple Rule-Based Recovery Simulation Results
    rule_baseline_status = Column(String(32), nullable=True) # RECOVERED, FAILED
    rule_baseline_action = Column(String(32), nullable=True) # RETRY, ALTERNATE_PAYMENT, REMINDER, ESCALATE, NO_ACTION
    rule_baseline_retries = Column(Integer, default=0)
    rule_baseline_recovered_amount = Column(Float, default=0.0)
    rule_baseline_intervention_cost = Column(Float, default=0.0)
    rule_baseline_net_recovered_amount = Column(Float, default=0.0)


class ProcessedEvent(Base):
    """
    Idempotency store to track processed payment/recovery event IDs with unique constraints.
    """
    __tablename__ = "processed_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(64), unique=True, index=True, nullable=False)
    payment_id = Column(Integer, ForeignKey("payment_records.id"), nullable=False, index=True)
    transaction_id = Column(String(64), index=True, nullable=False)
    action_approved = Column(String(32), nullable=False)
    simulation_status = Column(String(32), nullable=False)
    recovered_amount = Column(Float, default=0.0)
    intervention_cost = Column(Float, default=0.0)
    net_recovered_amount = Column(Float, default=0.0)
    response_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payment_records.id"), nullable=False, index=True)
    transaction_id = Column(String(64), nullable=False, index=True)
    event_id = Column(String(64), nullable=True, index=True)
    
    llm_mode = Column(String(64), nullable=False) # "LLM Mode (Provider)" or "Deterministic Fallback Mode"
    llm_diagnosis = Column(Text, nullable=False)
    llm_confidence = Column(Float, nullable=False)
    llm_action_recommended = Column(String(32), nullable=False)
    
    policy_action_approved = Column(String(32), nullable=False) # RETRY, ALTERNATE_PAYMENT, REMINDER, ESCALATE, NO_ACTION
    policy_override = Column(Boolean, default=False)
    policy_override_reason = Column(Text, nullable=True)
    
    simulation_status = Column(String(32), nullable=False) # RECOVERED, FAILED, ESCALATED, BLOCKED, DUPLICATE_BLOCKED
    simulated_probability = Column(Float, default=0.0)
    recovered_amount = Column(Float, default=0.0)          # Gross recovered
    intervention_cost = Column(Float, default=0.0)         # Synthetic action cost
    net_recovered_amount = Column(Float, default=0.0)      # Net = Gross - Cost
    
    duplicate_blocked = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    details_json = Column(Text, nullable=True)

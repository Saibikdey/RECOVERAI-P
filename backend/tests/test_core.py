import subprocess
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Query
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError

from app.database import Base, get_db
from app.main import app
from app.models import PaymentRecord, AuditLog, ProcessedEvent
from app.generator import generate_synthetic_payments
from app.schemas import RecoveryActionEnum, LLMDiagnosisOutput
from app.services.risk_engine import RiskEngine
from app.services.llm_service import LLMService
from app.services.policy_engine import PolicyEngine
from app.services.simulator import SimulationEngine, stable_seed
from app.services.orchestrator import RecoveryOrchestrator

# Test DB Setup (in-memory SQLite with StaticPool so all connections share the same memory DB)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    # Seed 100 test records
    records = generate_synthetic_payments(count=100, seed=42)
    db.add_all(records)
    db.commit()
    yield
    Base.metadata.drop_all(bind=test_engine)

client = TestClient(app)

# ==================== 1. SYNTHETIC DATASET TESTS ====================

def test_synthetic_payment_generation():
    """Verify that exactly 100 synthetic failed payment records are generated with valid data."""
    records = generate_synthetic_payments(count=100, seed=42)
    assert len(records) == 100
    
    for r in records:
        assert r.transaction_id.startswith("pay_fail_")
        assert r.customer_id.startswith("cust_")
        assert r.amount > 0.0
        assert r.currency == "INR"
        assert r.status == "FAILED"
        assert r.customer_tier in ["STANDARD", "VIP", "ENTERPRISE"]
        assert r.error_code in [
            "INSUFFICIENT_FUNDS", "CARD_EXPIRED", "BANK_SERVER_DOWN",
            "NETWORK_TIMEOUT", "AUTHENTICATION_FAILED_3DS", "LIMIT_EXCEEDED",
            "SUSPECTED_FRAUD", "DO_NOT_HONOR"
        ]

# ==================== 2. REVENUE AT RISK & RISK ENGINE TESTS ====================

def test_revenue_at_risk_calculation():
    """Verify that revenue at risk correctly calculates the total exposure."""
    db = TestingSessionLocal()
    payments = db.query(PaymentRecord).all()
    total_risk = sum(p.amount for p in payments)
    assert total_risk > 0.0
    
    for p in payments:
        risk_data = RiskEngine.evaluate_risk(p)
        assert "is_high_value" in risk_data
        assert "urgency" in risk_data
        assert 0.0 <= risk_data["recovery_feasibility"] <= 1.0

# ==================== 3. LLM SERVICE & DETERMINISTIC FALLBACK ====================

def test_llm_diagnosis_schema_and_fallback():
    """Verify that diagnosis produces valid structured output matching LLMDiagnosisOutput schema."""
    sample_payment = PaymentRecord(
        transaction_id="pay_test_001",
        customer_id="cust_001",
        customer_name="Aarav Sharma",
        customer_tier="STANDARD",
        amount=5000.0,
        currency="INR",
        payment_method="UPI",
        error_code="BANK_SERVER_DOWN",
        error_message="Issuer bank core switch not responding",
        status="FAILED",
        retry_count=0
    )
    
    diagnosis, mode = LLMService.diagnose_payment(sample_payment)
    assert isinstance(diagnosis, LLMDiagnosisOutput)
    assert diagnosis.root_cause_diagnosis != ""
    assert 0.0 <= diagnosis.confidence <= 1.0
    assert diagnosis.recommended_action in RecoveryActionEnum
    assert mode in ["LLM Mode", "Deterministic Fallback Mode"]

# ==================== 4. DETERMINISTIC POLICY ENGINE SAFETY GUARDRAILS ====================

def test_policy_engine_max_retries_guard():
    """Rule Check: If retry_count >= 3 and action is RETRY, Policy Engine must override."""
    exhausted_payment = PaymentRecord(
        transaction_id="pay_test_retries",
        customer_id="cust_002",
        customer_name="Rohan Verma",
        customer_tier="STANDARD",
        amount=2500.0,
        currency="INR",
        payment_method="UPI",
        error_code="BANK_SERVER_DOWN",
        error_message="Issuer switch timeout",
        retry_count=3
    )
    
    llm_diag = LLMDiagnosisOutput(
        root_cause_diagnosis="Temporary bank outage",
        confidence=0.88,
        recommended_action=RecoveryActionEnum.RETRY,
        rationale="Retry after cooldown"
    )
    
    decision = PolicyEngine.evaluate(exhausted_payment, llm_diag)
    assert decision.is_overridden is True
    assert decision.approved_action != RecoveryActionEnum.RETRY
    assert "Max Retries" in decision.override_reason

def test_policy_engine_fraud_protection():
    """Rule Check: Suspected fraud must NEVER allow RETRY or REMINDER."""
    fraud_payment = PaymentRecord(
        transaction_id="pay_test_fraud",
        customer_id="cust_003",
        customer_name="Anonymous Fraudster",
        customer_tier="STANDARD",
        amount=85000.0,
        currency="INR",
        payment_method="CREDIT_CARD",
        error_code="SUSPECTED_FRAUD",
        error_message="High velocity IP anomaly",
        retry_count=0
    )
    
    bad_llm_diag = LLMDiagnosisOutput(
        root_cause_diagnosis="Potential false positive",
        confidence=0.90,
        recommended_action=RecoveryActionEnum.RETRY,
        rationale="Attempt re-processing"
    )
    
    decision = PolicyEngine.evaluate(fraud_payment, bad_llm_diag)
    assert decision.is_overridden is True
    assert decision.approved_action == RecoveryActionEnum.NO_ACTION
    assert "Fraud Safety Guard" in decision.override_reason

def test_policy_engine_expired_card_no_retry():
    """Rule Check: Expired cards cannot be retried directly."""
    expired_payment = PaymentRecord(
        transaction_id="pay_test_expired",
        customer_id="cust_004",
        customer_name="Priya Patel",
        customer_tier="STANDARD",
        amount=3500.0,
        currency="INR",
        payment_method="CREDIT_CARD",
        error_code="CARD_EXPIRED",
        error_message="Card validity date is in the past",
        retry_count=0
    )
    
    llm_diag = LLMDiagnosisOutput(
        root_cause_diagnosis="Card expired",
        confidence=0.85,
        recommended_action=RecoveryActionEnum.RETRY,
        rationale="Retry card"
    )
    
    decision = PolicyEngine.evaluate(expired_payment, llm_diag)
    assert decision.is_overridden is True
    assert decision.approved_action == RecoveryActionEnum.ALTERNATE_PAYMENT

def test_policy_engine_confidence_threshold_guard():
    """Rule Check: Low confidence (< 0.65) must trigger ESCALATE for human review."""
    ambiguous_payment = PaymentRecord(
        transaction_id="pay_test_ambig",
        customer_id="cust_005",
        customer_name="Neha Gupta",
        customer_tier="STANDARD",
        amount=4000.0,
        currency="INR",
        payment_method="CREDIT_CARD",
        error_code="DO_NOT_HONOR",
        error_message="Generic decline (05)",
        retry_count=0
    )
    
    low_conf_diag = LLMDiagnosisOutput(
        root_cause_diagnosis="Unknown decline cause",
        confidence=0.55,
        recommended_action=RecoveryActionEnum.RETRY,
        rationale="Uncertain action"
    )
    
    decision = PolicyEngine.evaluate(ambiguous_payment, low_conf_diag)
    assert decision.is_overridden is True
    assert decision.approved_action == RecoveryActionEnum.ESCALATE
    assert "Confidence Guard" in decision.override_reason

def test_policy_engine_high_value_vip_guard():
    """Rule Check: High-value transaction (>= ₹50,000) or VIP with critical decline escalates."""
    vip_payment = PaymentRecord(
        transaction_id="pay_test_vip",
        customer_id="cust_vip_001",
        customer_name="Vikramaditya Singhania",
        customer_tier="VIP",
        amount=78000.0,
        currency="INR",
        payment_method="CREDIT_CARD",
        error_code="LIMIT_EXCEEDED",
        error_message="Transaction amount exceeds per-day limit",
        retry_count=0
    )
    
    retry_diag = LLMDiagnosisOutput(
        root_cause_diagnosis="Daily card spending limit hit",
        confidence=0.90,
        recommended_action=RecoveryActionEnum.RETRY,
        rationale="Blind retry"
    )
    
    decision = PolicyEngine.evaluate(vip_payment, retry_diag)
    assert decision.is_overridden is True
    assert decision.approved_action == RecoveryActionEnum.ESCALATE
    assert "High-Value Guard" in decision.override_reason

def test_llm_authority_boundary_invariant():
    """Invariant Check: An unauthorized action from LLM is blocked and overridden to ESCALATE."""
    sample_payment = PaymentRecord(
        transaction_id="pay_test_invariant",
        customer_id="cust_006",
        customer_name="Test Customer",
        customer_tier="STANDARD",
        amount=1000.0,
        currency="INR",
        payment_method="UPI",
        error_code="NETWORK_TIMEOUT",
        error_message="Gateway timeout",
        retry_count=0
    )
    
    bad_diag = LLMDiagnosisOutput.model_construct(
        root_cause_diagnosis="Attempt direct financial debit",
        confidence=0.99,
        recommended_action="FORCE_EXECUTE_PAYMENT",
        rationale="Bypass rule"
    )
    
    decision = PolicyEngine.evaluate(sample_payment, bad_diag)
    assert decision.is_overridden is True
    assert decision.approved_action == RecoveryActionEnum.ESCALATE
    assert decision.is_safe is False

# ==================== 5. IDEMPOTENCY & DUPLICATE EVENT PROTECTION TESTS ====================

def test_idempotency_first_event_success_and_duplicate_blocked():
    """Verify that an event executes first time, but identical event_id is blocked with DUPLICATE_BLOCKED."""
    db = TestingSessionLocal()
    payment = db.query(PaymentRecord).first()
    test_event_id = "evt_idemp_test_001"

    # First attempt: must succeed
    first_res = RecoveryOrchestrator.process_single_payment(payment, db, event_id=test_event_id)
    assert first_res.is_duplicate is False
    assert first_res.simulation_outcome.status in ["RECOVERED", "FAILED"]

    # Second attempt with same event_id: must be blocked
    second_res = RecoveryOrchestrator.process_single_payment(payment, db, event_id=test_event_id)
    assert second_res.is_duplicate is True
    assert second_res.simulation_outcome.status == "DUPLICATE_BLOCKED"
    assert "DUPLICATE_BLOCKED" in second_res.message

    # Verify duplicate attempt was recorded in audit log
    dup_audit = db.query(AuditLog).filter(
        AuditLog.event_id == test_event_id,
        AuditLog.duplicate_blocked == True
    ).first()
    assert dup_audit is not None
    assert dup_audit.simulation_status == "DUPLICATE_BLOCKED"

def test_idempotency_different_events_execute_independently():
    """Verify that different event_ids process independently."""
    db = TestingSessionLocal()
    payment = db.query(PaymentRecord).first()

    res1 = RecoveryOrchestrator.process_single_payment(payment, db, event_id="evt_distinct_101")
    res2 = RecoveryOrchestrator.process_single_payment(payment, db, event_id="evt_distinct_102")

    assert res1.is_duplicate is False
    assert res2.is_duplicate is False

# ==================== 6. BASELINE 2: RULE-BASED RECOVERY TESTS ====================

def test_rule_based_baseline_simulation():
    """Verify Baseline 2 simple rule-based recovery simulation."""
    db = TestingSessionLocal()
    res = RecoveryOrchestrator.run_rule_based_simulation(db)
    assert res["processed_count"] == 100
    assert res["recovered_count"] > 0
    assert res["total_recovered_revenue"] > 0.0

    # Verify DB records updated
    payments = db.query(PaymentRecord).all()
    for p in payments:
        assert p.rule_baseline_status in ["RECOVERED", "FAILED"]
        assert p.rule_baseline_action in [a.value for a in RecoveryActionEnum]

# ==================== 7. 3-WAY COMPARISON & MULTI-SEED EVALUATION ====================

def test_3_way_strategy_comparison():
    """Verify 3-way comparative analytics (Blind Retry vs Rule Baseline vs RecoverAI)."""
    db = TestingSessionLocal()
    
    # Run all 3 strategies
    RecoveryOrchestrator.run_batch_ai_recovery(db)
    RecoveryOrchestrator.run_baseline_simulation(db)
    RecoveryOrchestrator.run_rule_based_simulation(db)
    
    comp = RecoveryOrchestrator.get_comparison_summary(db)
    assert comp.total_records == 100
    assert comp.ai_strategy is not None
    assert comp.baseline_strategy is not None
    assert comp.rule_baseline_strategy is not None
    
    # RecoverAI should demonstrate measured uplift over both baselines
    assert comp.ai_strategy.recovery_rate_pct >= comp.rule_baseline_strategy.recovery_rate_pct
    assert comp.ai_strategy.recovery_rate_pct > comp.baseline_strategy.recovery_rate_pct
    assert comp.uplift_over_rule_revenue >= 0.0

def test_multi_seed_evaluation_runner():
    """Verify multi-seed statistical evaluation engine runs across seeds."""
    res = RecoveryOrchestrator.run_multi_seed_evaluation(seed_start=1, seed_end=3, count_per_seed=50)
    assert res.seed_count == 3
    assert len(res.per_seed_results) == 3
    assert res.ai_mean_recovery_rate > res.blind_mean_recovery_rate
    assert res.ai_mean_recovery_rate > res.rule_mean_recovery_rate
    assert res.mean_uplift_over_blind_rate > 0.0
    assert res.mean_uplift_over_rule_rate > 0.0

# ==================== 8. FASTAPI REST INTEGRATION ENDPOINTS ====================

def test_api_endpoints():
    """Verify all REST API endpoints function properly with new features."""
    # 1. Health check
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    
    # 2. Get Payments (100 records)
    res = client.get("/api/payments")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 100
    
    # 3. Diagnose Single Payment with Event ID
    payment_id = data[0]["id"]
    res = client.post(f"/api/recovery/diagnose/{payment_id}?event_id=evt_api_test_001")
    assert res.status_code == 200
    diag_res = res.json()
    assert diag_res["is_duplicate"] is False
    assert "llm_diagnosis" in diag_res
    assert "policy_evaluation" in diag_res

    # 4. Diagnose Duplicate Event ID -> Blocked
    res_dup = client.post(f"/api/recovery/diagnose/{payment_id}?event_id=evt_api_test_001")
    assert res_dup.status_code == 200
    assert res_dup.json()["is_duplicate"] is True
    assert res_dup.json()["simulation_outcome"]["status"] == "DUPLICATE_BLOCKED"
    
    # 5. Run Batch AI Recovery
    res = client.post("/api/recovery/batch")
    assert res.status_code == 200
    assert res.json()["processed_count"] == 100
    
    # 6. Run Blind Baseline
    res = client.post("/api/recovery/baseline")
    assert res.status_code == 200
    assert res.json()["processed_count"] == 100

    # 7. Run Rule-Based Baseline
    res = client.post("/api/recovery/rule-baseline")
    assert res.status_code == 200
    assert res.json()["processed_count"] == 100
    
    # 8. Get 3-Way Comparison
    res = client.get("/api/recovery/comparison")
    assert res.status_code == 200
    comp_data = res.json()
    assert "ai_strategy" in comp_data
    assert "baseline_strategy" in comp_data
    assert "rule_baseline_strategy" in comp_data
    assert comp_data["rule_baseline_strategy"]["name"] == "Simple Rule-Based Baseline"

    # 9. Get Multi-Seed Evaluation API
    res = client.get("/api/recovery/multi-seed-evaluation?seed_start=1&seed_end=2")
    assert res.status_code == 200
    multi_data = res.json()
    assert multi_data["seed_count"] == 2
    assert len(multi_data["per_seed_results"]) == 2
    
    # 10. Get Audit Logs with event_id
    res = client.get("/api/audit")
    assert res.status_code == 200
    assert len(res.json()) > 0
    
    # 11. Reset Synthetic Dataset (wipes payments & idempotency cache)
    res = client.post("/api/payments/reset")
    assert res.status_code == 200
    assert res.json()["count"] == 100

# ==================== 9. REPRODUCIBILITY REGRESSION TESTS ====================
# These guard against a real bug found in code review: Python's built-in
# hash() is randomized per-process for strings (PYTHONHASHSEED), so it
# cannot be used for the "same seed 42 -> same result every time" guarantee
# the README advertises. simulator.stable_seed() (SHA-256 based) replaced it.

def test_stable_seed_is_deterministic_within_process():
    """Same input must always produce the same stable_seed output."""
    val = "pay_fail_001_1234_RETRY_0"
    assert stable_seed(val) == stable_seed(val)
    # Different inputs should (almost always) differ
    assert stable_seed(val) != stable_seed(val + "_different")

def test_stable_seed_is_deterministic_across_processes():
    """
    Reproduces the exact bug found in review: spawn a fresh Python
    subprocess (a new PYTHONHASHSEED, simulating a server restart) and
    confirm stable_seed() still returns the identical value.

    Python's built-in hash() would fail this test (different value on
    almost every run); stable_seed() must pass it every time.
    """
    val = "pay_fail_001_1234_RETRY_0"
    expected = stable_seed(val)

    script = (
        "import sys; sys.path.insert(0, '.'); "
        "from app.services.simulator import stable_seed; "
        f"print(stable_seed({val!r}))"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd="backend" if __import__("os").path.isdir("backend") else ".",
    )
    assert result.returncode == 0, result.stderr
    subprocess_value = int(result.stdout.strip())
    assert subprocess_value == expected, (
        f"stable_seed() differed across processes: {expected} (this process) "
        f"vs {subprocess_value} (subprocess). Reproducibility is broken."
    )

def test_seed_42_simulation_outcomes_reproducible_across_runs():
    """
    End-to-end reproducibility check for the actual demo claim: generating
    the seed-42 dataset and simulating RecoverAI recovery twice (in two
    independent in-memory runs, mimicking two separate server sessions)
    must yield identical per-transaction outcomes and identical totals.
    """
    def run_once():
        records = generate_synthetic_payments(count=100, seed=42)
        total_recovered = 0.0
        statuses = []
        for r in records:
            diag, _ = LLMService.diagnose_payment(r)
            policy_res = PolicyEngine.evaluate(r, diag)
            outcome = SimulationEngine.simulate_ai_recovery(r, policy_res.approved_action)
            statuses.append(outcome.status)
            total_recovered += outcome.recovered_amount
        return statuses, round(total_recovered, 2)

    statuses_1, total_1 = run_once()
    statuses_2, total_2 = run_once()

    assert statuses_1 == statuses_2
    assert total_1 == total_2

# ==================== 10. IDEMPOTENCY ATOMICITY TEST ====================

def test_db_unique_constraint_rejects_duplicate_event_id():
    """
    Proves the actual mechanism that backs idempotency under a race:
    ProcessedEvent.event_id has a DB-level unique constraint, so two rows
    can never share an event_id -- even if both writers' pre-checks saw
    nothing (the TOCTOU window a pure application-level check can't close).
    """
    db = TestingSessionLocal()
    payment = db.query(PaymentRecord).first()
    race_event_id = "evt_db_constraint_race_001"

    winner = ProcessedEvent(
        event_id=race_event_id,
        payment_id=payment.id,
        transaction_id=payment.transaction_id,
        action_approved="RETRY",
        simulation_status="RECOVERED",
        recovered_amount=100.0,
    )
    db.add(winner)
    db.commit()

    loser = ProcessedEvent(
        event_id=race_event_id,  # identical event_id: the loser of a race
        payment_id=payment.id,
        transaction_id=payment.transaction_id,
        action_approved="RETRY",
        simulation_status="RECOVERED",
        recovered_amount=100.0,
    )
    db.add(loser)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    count = db.query(ProcessedEvent).filter(ProcessedEvent.event_id == race_event_id).count()
    assert count == 1

def test_orchestrator_handles_concurrent_race_gracefully():
    """
    Forces the exact TOCTOU race flagged in review: process_single_payment's
    pre-check is made to (incorrectly) report 'no existing event' for one
    call, even though a competing ProcessedEvent row for the same event_id
    is committed by a second, independent session moments earlier --
    reproducing two requests racing past the pre-check at the same time.

    Before this fix, the resulting IntegrityError at commit time would
    propagate as an unhandled 500. After this fix, process_single_payment
    must catch it and return a graceful DUPLICATE_BLOCKED response, with
    no double-counted revenue and no crash.
    """
    db = TestingSessionLocal()
    payment = db.query(PaymentRecord).first()
    race_event_id = "evt_orchestrator_race_001"

    # A second, independent session wins the race first.
    other_session = TestingSessionLocal()
    winner = ProcessedEvent(
        event_id=race_event_id,
        payment_id=payment.id,
        transaction_id=payment.transaction_id,
        action_approved="RETRY",
        simulation_status="RECOVERED",
        recovered_amount=100.0,
    )
    other_session.add(winner)
    other_session.commit()
    other_session.close()

    # Force this session's pre-check to miss the row that already exists,
    # simulating the TOCTOU window -- it proceeds believing it's first.
    original_first = Query.first
    state = {"bypassed": False}

    def patched_first(self):
        if not state["bypassed"]:
            state["bypassed"] = True
            return None
        return original_first(self)

    with patch.object(Query, "first", patched_first):
        result = RecoveryOrchestrator.process_single_payment(payment, db, event_id=race_event_id)

    assert result.is_duplicate is True
    assert result.simulation_outcome.status == "DUPLICATE_BLOCKED"

    # Still exactly one ProcessedEvent row for this event_id -- no
    # double-processing occurred despite the forced race.
    count = db.query(ProcessedEvent).filter(ProcessedEvent.event_id == race_event_id).count()
    assert count == 1

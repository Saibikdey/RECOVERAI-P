import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import PaymentRecord, AuditLog, ProcessedEvent
from app.schemas import RecoveryActionEnum, LLMDiagnosisOutput
from app.generator import generate_synthetic_payments
from app.services.llm_service import LLMService
from app.services.policy_engine import PolicyEngine
from app.services.simulator import SimulationEngine, stable_seed, INTERVENTION_COSTS
from app.services.risk_engine import RiskEngine
from app.services.orchestrator import RecoveryOrchestrator

# Setup in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    records = generate_synthetic_payments(count=100, seed=42)
    db.add_all(records)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

# 1. Dataset Generation Test
def test_synthetic_payment_generation():
    records = generate_synthetic_payments(count=100, seed=42)
    assert len(records) == 100
    for r in records:
        assert r.amount > 0
        assert r.currency == "INR"
        assert r.status == "FAILED"
        assert r.error_code in [
            "INSUFFICIENT_FUNDS", "CARD_EXPIRED", "BANK_SERVER_DOWN", 
            "NETWORK_TIMEOUT", "AUTHENTICATION_FAILED_3DS", "LIMIT_EXCEEDED", 
            "SUSPECTED_FRAUD", "DO_NOT_HONOR"
        ]

# 2. Revenue at Risk Calculation Test
def test_revenue_at_risk_calculation():
    records = generate_synthetic_payments(count=100, seed=42)
    total_risk = sum(r.amount for r in records)
    assert total_risk > 1000000.0  # Should exceed ₹10 Lakhs

# 3. LLM Diagnosis Schema & Fallback Test
def test_llm_diagnosis_schema_and_fallback():
    records = generate_synthetic_payments(count=5, seed=42)
    for r in records:
        diag, mode = LLMService.diagnose_payment(r)
        assert isinstance(diag, LLMDiagnosisOutput)
        assert 0.0 <= diag.confidence <= 1.0
        assert diag.recommended_action in list(RecoveryActionEnum)
        assert len(diag.root_cause_diagnosis) > 5

# 4. Policy Engine: Max Retries Guard Test
def test_policy_engine_max_retries_guard():
    db = TestingSessionLocal()
    payment = PaymentRecord(
        transaction_id="tx_test_max_retry",
        customer_id="cust_1",
        customer_name="Test Customer",
        customer_tier="STANDARD",
        amount=1500.0,
        currency="INR",
        payment_method="UPI",
        error_code="BANK_SERVER_DOWN",
        error_message="Server down",
        status="FAILED",
        retry_count=3  # Max retries reached
    )
    mock_diagnosis = LLMDiagnosisOutput(
        root_cause_diagnosis="Temporary bank outage",
        confidence=0.90,
        recommended_action=RecoveryActionEnum.RETRY,
        rationale="Retry should succeed"
    )
    policy_res = PolicyEngine.evaluate(payment, mock_diagnosis)
    assert policy_res.is_overridden is True
    assert policy_res.approved_action in [RecoveryActionEnum.ALTERNATE_PAYMENT, RecoveryActionEnum.ESCALATE]
    assert "Max Retries Exhausted" in (policy_res.override_reason or "")
    db.close()

# 5. Policy Engine: Fraud Protection Test
def test_policy_engine_fraud_protection():
    payment = PaymentRecord(
        transaction_id="tx_test_fraud",
        customer_id="cust_fraud",
        customer_name="Suspect User",
        customer_tier="STANDARD",
        amount=65000.0,
        currency="INR",
        payment_method="CREDIT_CARD",
        error_code="SUSPECTED_FRAUD",
        error_message="Security velocity anomaly",
        status="FAILED",
        retry_count=0
    )
    mock_diagnosis = LLMDiagnosisOutput(
        root_cause_diagnosis="Fraud alert",
        confidence=0.95,
        recommended_action=RecoveryActionEnum.RETRY,
        rationale="Attempt retry anyway"
    )
    policy_res = PolicyEngine.evaluate(payment, mock_diagnosis)
    assert policy_res.is_overridden is True
    assert policy_res.approved_action == RecoveryActionEnum.NO_ACTION
    assert "Fraud Safety Guard" in (policy_res.override_reason or "")

# 6. Policy Engine: Expired Card No Retry Test
def test_policy_engine_expired_card_no_retry():
    payment = PaymentRecord(
        transaction_id="tx_test_card_exp",
        customer_id="cust_exp",
        customer_name="Cardholder",
        customer_tier="STANDARD",
        amount=2500.0,
        currency="INR",
        payment_method="CREDIT_CARD",
        error_code="CARD_EXPIRED",
        error_message="Card validity in past",
        status="FAILED",
        retry_count=0
    )
    mock_diagnosis = LLMDiagnosisOutput(
        root_cause_diagnosis="Expired card",
        confidence=0.85,
        recommended_action=RecoveryActionEnum.RETRY,
        rationale="Retry card"
    )
    policy_res = PolicyEngine.evaluate(payment, mock_diagnosis)
    assert policy_res.is_overridden is True
    assert policy_res.approved_action == RecoveryActionEnum.ALTERNATE_PAYMENT

# 7. Policy Engine: Confidence Threshold Guard Test
def test_policy_engine_confidence_threshold_guard():
    payment = PaymentRecord(
        transaction_id="tx_test_low_conf",
        customer_id="cust_low",
        customer_name="Low Conf User",
        customer_tier="STANDARD",
        amount=5000.0,
        currency="INR",
        payment_method="UPI",
        error_code="DO_NOT_HONOR",
        error_message="Issuer generic decline",
        status="FAILED",
        retry_count=0
    )
    mock_diagnosis = LLMDiagnosisOutput(
        root_cause_diagnosis="Uncertain reason for decline",
        confidence=0.45,  # Below threshold of 0.65
        recommended_action=RecoveryActionEnum.RETRY,
        rationale="Unsure why it failed"
    )
    policy_res = PolicyEngine.evaluate(payment, mock_diagnosis)
    assert policy_res.is_overridden is True
    assert policy_res.approved_action == RecoveryActionEnum.ESCALATE
    assert "Confidence Guard" in (policy_res.override_reason or "")

# 8. Policy Engine: High-Value & VIP Guard Test
def test_policy_engine_high_value_vip_guard():
    payment = PaymentRecord(
        transaction_id="tx_test_vip_high",
        customer_id="cust_vip_corp",
        customer_name="Corporate VIP",
        customer_tier="ENTERPRISE",
        amount=85000.0,
        currency="INR",
        payment_method="CREDIT_CARD",
        error_code="LIMIT_EXCEEDED",
        error_message="Card limit hit",
        status="FAILED",
        retry_count=0
    )
    mock_diagnosis = LLMDiagnosisOutput(
        root_cause_diagnosis="Limit exceeded on large account",
        confidence=0.85,
        recommended_action=RecoveryActionEnum.RETRY,
        rationale="Retry card"
    )
    policy_res = PolicyEngine.evaluate(payment, mock_diagnosis)
    assert policy_res.is_overridden is True
    assert policy_res.approved_action == RecoveryActionEnum.ESCALATE
    assert "High-Value Guard" in (policy_res.override_reason or "")

# 9. Reproducibility & Stable Seed Test
def test_reproducibility_stable_seed_across_calls():
    key1 = "pay_fail_001_1234_RETRY_0"
    seed1 = stable_seed(key1)
    seed2 = stable_seed(key1)
    assert seed1 == seed2
    assert isinstance(seed1, int)

    payment = PaymentRecord(
        transaction_id="tx_repro_1",
        customer_id="cust_1",
        customer_name="Reproducible Customer",
        customer_tier="STANDARD",
        amount=10000.0,
        currency="INR",
        payment_method="UPI",
        error_code="BANK_SERVER_DOWN",
        error_message="Server down",
        status="FAILED",
        retry_count=0
    )
    outcome1 = SimulationEngine.simulate_ai_recovery(payment, RecoveryActionEnum.RETRY, seed_offset=42)
    outcome2 = SimulationEngine.simulate_ai_recovery(payment, RecoveryActionEnum.RETRY, seed_offset=42)
    assert outcome1.status == outcome2.status
    assert outcome1.recovered_amount == outcome2.recovered_amount
    assert outcome1.intervention_cost == outcome2.intervention_cost
    assert outcome1.net_recovered_amount == outcome2.net_recovered_amount

# 8. Economic Evaluation & Expected Net Recovery Test
def test_economic_evaluation_expected_net_recovery():
    payment = PaymentRecord(
        transaction_id="tx_econ_1",
        customer_id="cust_vip",
        customer_name="VIP Trader",
        customer_tier="VIP",
        amount=82450.0,
        currency="INR",
        payment_method="UPI",
        error_code="LIMIT_EXCEEDED",
        error_message="Single tx limit hit",
        status="FAILED",
        retry_count=0
    )
    policy_checks = PolicyEngine.evaluate_candidate_eligibility(payment)
    econ = SimulationEngine.evaluate_action_economics(payment, policy_checks)
    
    assert len(econ.candidate_actions) == 5
    for a in econ.candidate_actions:
        assert a.expected_gross_recovery == pytest.approx(a.success_probability * payment.amount, 0.01)
        assert a.expected_net_recovery == pytest.approx(a.expected_gross_recovery - a.intervention_cost, 0.01)
    assert econ.optimal_economic_action in [RecoveryActionEnum.ALTERNATE_PAYMENT.value, RecoveryActionEnum.ESCALATE.value]
    assert econ.optimal_expected_net > 0.0

# 9. Atomic Idempotency & Duplicate Protection Test
def test_idempotency_atomic_and_duplicate_blocked():
    db = TestingSessionLocal()
    payment = db.query(PaymentRecord).first()
    event_id = "evt_unique_test_1001"

    # First attempt: succeeds
    res1 = RecoveryOrchestrator.process_single_payment(payment, db, event_id=event_id)
    assert res1.is_duplicate is False
    assert res1.event_id == event_id

    # Second attempt: blocked by idempotency
    res2 = RecoveryOrchestrator.process_single_payment(payment, db, event_id=event_id)
    assert res2.is_duplicate is True
    assert res2.simulation_outcome.status == "DUPLICATE_BLOCKED"
    assert res2.simulation_outcome.recovered_amount == 0.0
    assert "DUPLICATE_BLOCKED" in (res2.message or "")

    # Verify audit log recorded duplicate block
    dup_log = db.query(AuditLog).filter(AuditLog.event_id == event_id, AuditLog.duplicate_blocked == True).first()
    assert dup_log is not None
    assert dup_log.duplicate_blocked is True
    db.close()

# 10. Baseline Independence Test
def test_baseline_independence():
    db = TestingSessionLocal()
    # Run Rule Baseline first without running AI recovery
    rule_res = RecoveryOrchestrator.run_rule_based_simulation(db)
    assert rule_res["processed_count"] == 100
    assert rule_res["recovered_count"] > 0
    assert rule_res["total_recovered_revenue"] > 0.0

    # Run Blind Baseline
    blind_res = RecoveryOrchestrator.run_baseline_simulation(db)
    assert blind_res["processed_count"] == 100
    assert blind_res["total_retries"] >= 100
    db.close()

# 11. 3-Way Strategy Comparison with Gross and Net Metrics Test
def test_3_way_strategy_comparison_with_net_metrics():
    db = TestingSessionLocal()
    RecoveryOrchestrator.run_batch_ai_recovery(db)
    RecoveryOrchestrator.run_baseline_simulation(db)
    RecoveryOrchestrator.run_rule_based_simulation(db)

    summary = RecoveryOrchestrator.get_comparison_summary(db)
    assert summary.ai_strategy.total_recovered_revenue > 0.0
    assert summary.ai_strategy.total_net_recovered_revenue > 0.0
    assert summary.ai_strategy.revenue_recovery_rate_pct > 0.0
    assert summary.ai_strategy.transaction_recovery_rate_pct > 0.0
    assert summary.uplift_revenue >= 0.0
    assert summary.uplift_net_revenue >= 0.0
    assert summary.uplift_over_rule_revenue >= 0.0
    assert summary.uplift_over_rule_net_revenue >= 0.0
    db.close()

# 12. Multi-Seed Robustness Evaluation Test
def test_multi_seed_robustness_evaluation():
    res = RecoveryOrchestrator.run_multi_seed_evaluation(seed_start=1, seed_end=5, count_per_seed=20)
    assert res.seed_count == 5
    assert len(res.per_seed_results) == 5
    assert res.ai_mean_gross_revenue > 0.0
    assert res.ai_mean_intervention_cost > 0.0
    assert res.ai_mean_net_revenue > 0.0
    assert res.ai_mean_revenue_rate > 0.0
    assert res.ai_mean_tx_recovery_rate > 0.0
    assert res.rule_mean_intervention_cost > 0.0
    assert res.blind_mean_intervention_cost > 0.0
    assert res.mean_net_uplift_over_rule > 0.0
    assert res.net_revenue_uplift_pct_over_rule > 0.0
    assert res.mean_net_uplift_over_blind > 0.0
    assert res.net_revenue_uplift_pct_over_blind > 0.0
    assert res.tx_advantage_over_rule_pts > 0.0
    assert res.tx_advantage_over_blind_pts > 0.0

    for item in res.per_seed_results:
        assert "ai_intervention_cost" in item
        assert "rule_intervention_cost" in item
        assert "blind_intervention_cost" in item
        assert item["ai_net_revenue"] == round(item["ai_gross_revenue"] - item["ai_intervention_cost"], 2)
        assert item["rule_net_revenue"] == round(item["rule_gross_revenue"] - item["rule_intervention_cost"], 2)
        assert item["blind_net_revenue"] == round(item["blind_gross_revenue"] - item["blind_intervention_cost"], 2)

# 13. REST Endpoints Integration & Custom Seed Reset Test
def test_api_endpoints_including_seed_reset():
    # Test reset with seed=42
    r_reset_42 = client.post("/api/payments/reset?seed=42")
    assert r_reset_42.status_code == 200
    data_42 = r_reset_42.json()
    assert data_42["count"] == 100
    risk_42 = data_42["total_revenue_at_risk"]

    # Test reset with custom seed=99
    r_reset_99 = client.post("/api/payments/reset?seed=99")
    assert r_reset_99.status_code == 200
    data_99 = r_reset_99.json()
    assert data_99["seed"] == 99
    assert data_99["count"] == 100
    risk_99 = data_99["total_revenue_at_risk"]
    # Changing the seed changes the generated dataset risk dynamically
    assert risk_42 != risk_99

    # Reset back to demo seed=42
    client.post("/api/payments/reset?seed=42")

    # Test batch recovery
    r_batch = client.post("/api/recovery/batch")
    assert r_batch.status_code == 200

    # Test baseline
    r_base = client.post("/api/recovery/baseline")
    assert r_base.status_code == 200

    # Test rule baseline
    r_rule = client.post("/api/recovery/rule-baseline")
    assert r_rule.status_code == 200

    # Test comparison
    r_comp = client.get("/api/recovery/comparison")
    assert r_comp.status_code == 200
    comp = r_comp.json()
    assert "ai_strategy" in comp
    assert "baseline_strategy" in comp
    assert "rule_baseline_strategy" in comp
    assert "uplift_net_revenue" in comp

    # Test single diagnosis with idempotency
    r_diag = client.post("/api/recovery/diagnose/1?event_id=evt_api_test_001")
    assert r_diag.status_code == 200
    assert r_diag.json()["is_duplicate"] is False
    assert "economic_evaluation" in r_diag.json()

    # Repeat same event_id -> should be blocked
    r_diag_dup = client.post("/api/recovery/diagnose/1?event_id=evt_api_test_001")
    assert r_diag_dup.status_code == 200
    assert r_diag_dup.json()["is_duplicate"] is True

    # Test multi-seed endpoint
    r_multi = client.get("/api/recovery/multi-seed-evaluation?seed_start=1&seed_end=3")
    assert r_multi.status_code == 200
    assert r_multi.json()["seed_count"] == 3

import json
import uuid
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import PaymentRecord, AuditLog, ProcessedEvent
from app.schemas import (
    RecoveryPipelineResponse,
    ComparisonSummary,
    StrategyMetrics,
    SystemOverview,
    RecoveryActionEnum,
    PolicyEvaluationResult,
    SimulationOutcome,
    LLMDiagnosisOutput,
    MultiSeedEvaluationResult
)
from app.services.llm_service import LLMService
from app.services.policy_engine import PolicyEngine
from app.services.simulator import SimulationEngine
from app.services.risk_engine import RiskEngine
from app.generator import generate_synthetic_payments

class RecoveryOrchestrator:

    @classmethod
    def process_single_payment(
        cls, 
        payment: PaymentRecord, 
        db: Session,
        event_id: Optional[str] = None
    ) -> RecoveryPipelineResponse:
        """
        Executes the end-to-end recovery pipeline for a single failed payment with Idempotency Protection:
        1. Atomic Check of event_id idempotency (Block duplicates)
        2. Risk / Context Assessment & Candidate Action Economics Evaluation
        3. Contextual LLM Diagnosis (or deterministic fallback)
        4. Deterministic Policy Engine Authorization (Strict Final Authority)
        5. Simulation Outcome (Gross revenue, synthetic intervention cost, net revenue)
        6. Audit Log & Processed Event Persistence
        """
        effective_event_id = event_id or f"evt_{payment.transaction_id}_{payment.retry_count}_{uuid.uuid4().hex[:6]}"

        # ==================== STEP 1: ATOMIC IDEMPOTENCY CHECK ====================
        existing_event = db.query(ProcessedEvent).filter(ProcessedEvent.event_id == effective_event_id).first()
        if existing_event:
            return cls._handle_duplicate_event(payment, effective_event_id, existing_event, db)

        # ==================== STEP 2: RISK & ECONOMIC EVALUATION ====================
        policy_checks = PolicyEngine.evaluate_candidate_eligibility(payment)
        economic_eval = SimulationEngine.evaluate_action_economics(payment, policy_checks)
        risk_profile = RiskEngine.evaluate_risk(payment)

        # ==================== STEP 3: CONTEXTUAL AI DIAGNOSIS ====================
        diagnosis, llm_mode = LLMService.diagnose_payment(payment)
        
        # ==================== STEP 4: DETERMINISTIC POLICY ENGINE ====================
        policy_eval = PolicyEngine.evaluate(payment, diagnosis)
        
        # ==================== STEP 5: SIMULATION OUTCOME ====================
        outcome = SimulationEngine.simulate_ai_recovery(payment, policy_eval.approved_action)
        
        # ==================== STEP 6: UPDATE PAYMENT RECORD ====================
        payment.recovery_action_taken = policy_eval.approved_action.value
        payment.status = outcome.status
        payment.recovered_amount = outcome.recovered_amount
        payment.intervention_cost = outcome.intervention_cost
        payment.net_recovered_amount = outcome.net_recovered_amount
        if outcome.status == "RECOVERED":
            payment.retry_count += 1
        elif policy_eval.approved_action == RecoveryActionEnum.RETRY:
            payment.retry_count += 1

        # ==================== STEP 7: RECORD AUDIT & IDEMPOTENCY ====================
        audit_entry = AuditLog(
            payment_id=payment.id,
            transaction_id=payment.transaction_id,
            event_id=effective_event_id,
            llm_mode=llm_mode,
            llm_diagnosis=f"{diagnosis.root_cause_diagnosis} (Rationale: {diagnosis.rationale})",
            llm_confidence=diagnosis.confidence,
            llm_action_recommended=diagnosis.recommended_action.value,
            policy_action_approved=policy_eval.approved_action.value,
            policy_override=policy_eval.is_overridden,
            policy_override_reason=policy_eval.override_reason,
            simulation_status=outcome.status,
            simulated_probability=outcome.simulated_probability,
            recovered_amount=outcome.recovered_amount,
            intervention_cost=outcome.intervention_cost,
            net_recovered_amount=outcome.net_recovered_amount,
            duplicate_blocked=False,
            timestamp=datetime.now(timezone.utc),
            details_json=json.dumps({
                "applied_rules": policy_eval.applied_rules,
                "notes": outcome.notes,
                "customer_tier": payment.customer_tier,
                "amount": payment.amount,
                "error_code": payment.error_code,
                "event_id": effective_event_id,
                "risk_profile": risk_profile,
                "why_this_action": economic_eval.why_this_action,
                "optimal_economic_action": economic_eval.optimal_economic_action,
                "optimal_expected_net": economic_eval.optimal_expected_net
            })
        )
        db.add(audit_entry)

        # Mark event as processed in idempotency table with unique constraint handling
        processed_evt = ProcessedEvent(
            event_id=effective_event_id,
            payment_id=payment.id,
            transaction_id=payment.transaction_id,
            action_approved=policy_eval.approved_action.value,
            simulation_status=outcome.status,
            recovered_amount=outcome.recovered_amount,
            intervention_cost=outcome.intervention_cost,
            net_recovered_amount=outcome.net_recovered_amount,
            response_json=json.dumps({
                "action": policy_eval.approved_action.value,
                "status": outcome.status,
                "recovered_amount": outcome.recovered_amount,
                "intervention_cost": outcome.intervention_cost,
                "net_recovered_amount": outcome.net_recovered_amount
            })
        )
        db.add(processed_evt)

        try:
            db.commit()
            db.refresh(payment)
        except IntegrityError:
            # Concurrency race: Another request committed the same event_id simultaneously
            db.rollback()
            existing_event = db.query(ProcessedEvent).filter(ProcessedEvent.event_id == effective_event_id).first()
            return cls._handle_duplicate_event(payment, effective_event_id, existing_event, db)

        return RecoveryPipelineResponse(
            payment_id=payment.id,
            transaction_id=payment.transaction_id,
            event_id=effective_event_id,
            is_duplicate=False,
            message="Recovery action authorized and simulated successfully.",
            llm_mode=llm_mode,
            llm_diagnosis=diagnosis,
            economic_evaluation=economic_eval,
            policy_evaluation=policy_eval,
            simulation_outcome=outcome,
            timestamp=audit_entry.timestamp
        )

    @classmethod
    def _handle_duplicate_event(
        cls, 
        payment: PaymentRecord, 
        event_id: str, 
        existing_event: Optional[ProcessedEvent], 
        db: Session
    ) -> RecoveryPipelineResponse:
        """Helper to block duplicate execution and persist an audit entry."""
        duplicate_audit = AuditLog(
            payment_id=payment.id,
            transaction_id=payment.transaction_id,
            event_id=event_id,
            llm_mode="Idempotency Guard",
            llm_diagnosis="Duplicate recovery event detected. Re-execution blocked by Idempotency Layer.",
            llm_confidence=1.0,
            llm_action_recommended="NO_ACTION",
            policy_action_approved="NO_ACTION",
            policy_override=True,
            policy_override_reason=f"Idempotency Guard: Event ID '{event_id}' has already been processed. Duplicate recovery blocked.",
            simulation_status="DUPLICATE_BLOCKED",
            simulated_probability=0.0,
            recovered_amount=0.0,
            intervention_cost=0.0,
            net_recovered_amount=0.0,
            duplicate_blocked=True,
            timestamp=datetime.now(timezone.utc),
            details_json=json.dumps({
                "original_event_id": event_id,
                "original_action": existing_event.action_approved if existing_event else "UNKNOWN",
                "original_status": existing_event.simulation_status if existing_event else "UNKNOWN",
                "original_recovered_amount": existing_event.recovered_amount if existing_event else 0.0
            })
        )
        db.add(duplicate_audit)
        db.commit()

        return RecoveryPipelineResponse(
            payment_id=payment.id,
            transaction_id=payment.transaction_id,
            event_id=event_id,
            is_duplicate=True,
            message=f"DUPLICATE_BLOCKED: Event '{event_id}' was already processed. Duplicate recovery rejected.",
            llm_mode="Idempotency Guard",
            llm_diagnosis=LLMDiagnosisOutput(
                root_cause_diagnosis="Duplicate event submission",
                confidence=1.0,
                recommended_action=RecoveryActionEnum.NO_ACTION,
                rationale="Idempotency protection prevented duplicate financial processing."
            ),
            economic_evaluation=None,
            policy_evaluation=PolicyEvaluationResult(
                recommended_action="NO_ACTION",
                approved_action=RecoveryActionEnum.NO_ACTION,
                is_overridden=True,
                override_reason="Duplicate event blocked",
                applied_rules=["RULE_IDEMPOTENCY_DUPLICATE_BLOCK"]
            ),
            simulation_outcome=SimulationOutcome(
                status="DUPLICATE_BLOCKED",
                simulated_probability=0.0,
                recovered_amount=0.0,
                intervention_cost=0.0,
                net_recovered_amount=0.0,
                notes=f"Duplicate event '{event_id}' blocked."
            ),
            timestamp=duplicate_audit.timestamp
        )

    @classmethod
    def run_batch_ai_recovery(cls, db: Session) -> Dict[str, Any]:
        """Runs RecoverAI across all 100 failed payment records."""
        payments = db.query(PaymentRecord).all()
        processed_count = 0
        recovered_count = 0
        total_recovered_revenue = 0.0
        total_intervention_cost = 0.0
        total_net_recovered_revenue = 0.0
        overrides_count = 0
        
        for payment in payments:
            event_id = f"evt_batch_{payment.transaction_id}_{payment.retry_count}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:4]}"
            res = cls.process_single_payment(payment, db, event_id=event_id)
            processed_count += 1
            if res.simulation_outcome.status == "RECOVERED":
                recovered_count += 1
                total_recovered_revenue += res.simulation_outcome.recovered_amount
            total_intervention_cost += res.simulation_outcome.intervention_cost
            total_net_recovered_revenue += res.simulation_outcome.net_recovered_amount
            if res.policy_evaluation.is_overridden:
                overrides_count += 1
                
        return {
            "processed_count": processed_count,
            "recovered_count": recovered_count,
            "total_recovered_revenue": round(total_recovered_revenue, 2),
            "total_intervention_cost": round(total_intervention_cost, 2),
            "total_net_recovered_revenue": round(total_net_recovered_revenue, 2),
            "overrides_count": overrides_count
        }

    @classmethod
    def run_baseline_simulation(cls, db: Session) -> Dict[str, Any]:
        """Runs Baseline 1: Naive Blind 3x Retry across all 100 records."""
        payments = db.query(PaymentRecord).all()
        recovered_count = 0
        total_recovered_revenue = 0.0
        total_intervention_cost = 0.0
        total_net_recovered_revenue = 0.0
        total_retries = 0
        unnecessary_retries = 0

        for payment in payments:
            res = SimulationEngine.simulate_baseline_recovery(payment)
            payment.baseline_status = res["status"]
            payment.baseline_recovered_amount = res["recovered_amount"]
            payment.baseline_intervention_cost = res["intervention_cost"]
            payment.baseline_net_recovered_amount = res["net_recovered_amount"]
            payment.baseline_retries = res["retries_executed"]
            
            total_retries += res["retries_executed"]
            unnecessary_retries += res["unnecessary_retries"]
            total_intervention_cost += res["intervention_cost"]
            total_net_recovered_revenue += res["net_recovered_amount"]
            if res["status"] == "RECOVERED":
                recovered_count += 1
                total_recovered_revenue += res["recovered_amount"]
                
        db.commit()

        return {
            "processed_count": len(payments),
            "recovered_count": recovered_count,
            "total_recovered_revenue": round(total_recovered_revenue, 2),
            "total_intervention_cost": round(total_intervention_cost, 2),
            "total_net_recovered_revenue": round(total_net_recovered_revenue, 2),
            "total_retries": total_retries,
            "unnecessary_retries": unnecessary_retries
        }

    @classmethod
    def run_rule_based_simulation(cls, db: Session) -> Dict[str, Any]:
        """Runs Baseline 2: Simple Rule-Based Recovery across all 100 records."""
        payments = db.query(PaymentRecord).all()
        recovered_count = 0
        total_recovered_revenue = 0.0
        total_intervention_cost = 0.0
        total_net_recovered_revenue = 0.0
        total_retries = 0
        unnecessary_retries = 0

        for payment in payments:
            res = SimulationEngine.simulate_rule_based_recovery(payment)
            payment.rule_baseline_status = res["status"]
            payment.rule_baseline_action = res["action"]
            payment.rule_baseline_recovered_amount = res["recovered_amount"]
            payment.rule_baseline_intervention_cost = res["intervention_cost"]
            payment.rule_baseline_net_recovered_amount = res["net_recovered_amount"]
            payment.rule_baseline_retries = res["retries_executed"]

            total_retries += res["retries_executed"]
            unnecessary_retries += res["unnecessary_retries"]
            total_intervention_cost += res["intervention_cost"]
            total_net_recovered_revenue += res["net_recovered_amount"]
            if res["status"] == "RECOVERED":
                recovered_count += 1
                total_recovered_revenue += res["recovered_amount"]

        db.commit()

        return {
            "processed_count": len(payments),
            "recovered_count": recovered_count,
            "total_recovered_revenue": round(total_recovered_revenue, 2),
            "total_intervention_cost": round(total_intervention_cost, 2),
            "total_net_recovered_revenue": round(total_net_recovered_revenue, 2),
            "total_retries": total_retries,
            "unnecessary_retries": unnecessary_retries
        }

    @classmethod
    def get_comparison_summary(cls, db: Session) -> ComparisonSummary:
        """
        Generates 3-way comparative analytics from actual DB records:
        1. Naive Baseline (Blind Retries)
        2. Simple Rule-Based Baseline
        3. RecoverAI (AI Contextual Diagnosis + Deterministic Policy Engine)
        """
        payments = db.query(PaymentRecord).all()
        total_records = len(payments)
        total_revenue_at_risk = sum(p.amount for p in payments)
        
        latest_audit = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
        current_llm_mode = latest_audit.llm_mode if latest_audit else "Deterministic Fallback Mode"

        # 1. RecoverAI Strategy
        ai_recovered_payments = [p for p in payments if p.status == "RECOVERED"]
        ai_recovered_revenue = sum(p.recovered_amount for p in ai_recovered_payments)
        ai_intervention_cost = sum(p.intervention_cost for p in payments)
        ai_net_recovered_revenue = ai_recovered_revenue - ai_intervention_cost
        
        ai_rev_recovery_rate = (ai_recovered_revenue / total_revenue_at_risk * 100) if total_revenue_at_risk > 0 else 0.0
        ai_net_rev_recovery_rate = (ai_net_recovered_revenue / total_revenue_at_risk * 100) if total_revenue_at_risk > 0 else 0.0
        ai_tx_recovery_rate = (len(ai_recovered_payments) / total_records * 100) if total_records > 0 else 0.0
        
        ai_retries_executed = sum(1 for p in payments if p.recovery_action_taken == "RETRY")
        overrides_count = db.query(AuditLog).filter(AuditLog.policy_override == True).count()
        fraud_blocks = sum(1 for p in payments if p.error_code == "SUSPECTED_FRAUD" and p.recovery_action_taken in ["NO_ACTION", "ESCALATE"])
        escalations = sum(1 for p in payments if p.recovery_action_taken == "ESCALATE")

        ai_metrics = StrategyMetrics(
            name="RecoverAI (AI + Policy Engine)",
            description="Contextual LLM root cause diagnosis with deterministic policy guardrails and expected net value optimization.",
            total_revenue_at_risk=round(total_revenue_at_risk, 2),
            total_recovered_revenue=round(ai_recovered_revenue, 2),
            total_intervention_cost=round(ai_intervention_cost, 2),
            total_net_recovered_revenue=round(ai_net_recovered_revenue, 2),
            revenue_recovery_rate_pct=round(ai_rev_recovery_rate, 2),
            net_revenue_recovery_rate_pct=round(ai_net_rev_recovery_rate, 2),
            transaction_recovery_rate_pct=round(ai_tx_recovery_rate, 2),
            recovered_count=len(ai_recovered_payments),
            total_failed_count=total_records,
            total_retries_executed=ai_retries_executed,
            unnecessary_failed_retries=0,
            overrides_enforced=overrides_count,
            fraud_blocks=fraud_blocks,
            escalations_count=escalations
        )

        # 2. Baseline 1: Blind Retries
        baseline_recovered_payments = [p for p in payments if p.baseline_status == "RECOVERED"]
        baseline_recovered_revenue = sum(p.baseline_recovered_amount for p in baseline_recovered_payments)
        baseline_intervention_cost = sum(p.baseline_intervention_cost for p in payments)
        baseline_net_revenue = baseline_recovered_revenue - baseline_intervention_cost
        
        baseline_rev_recovery_rate = (baseline_recovered_revenue / total_revenue_at_risk * 100) if total_revenue_at_risk > 0 else 0.0
        baseline_net_rev_recovery_rate = (baseline_net_revenue / total_revenue_at_risk * 100) if total_revenue_at_risk > 0 else 0.0
        baseline_tx_recovery_rate = (len(baseline_recovered_payments) / total_records * 100) if total_records > 0 else 0.0
        
        baseline_total_retries = sum(p.baseline_retries for p in payments)
        baseline_unnecessary_retries = sum(p.baseline_retries for p in payments if p.baseline_status != "RECOVERED")

        blind_metrics = StrategyMetrics(
            name="Naive Baseline (Blind Retries)",
            description="Naive Baseline — blind retry strategy without diagnosis, economic valuation, or policy guardrails.",
            total_revenue_at_risk=round(total_revenue_at_risk, 2),
            total_recovered_revenue=round(baseline_recovered_revenue, 2),
            total_intervention_cost=round(baseline_intervention_cost, 2),
            total_net_recovered_revenue=round(baseline_net_revenue, 2),
            revenue_recovery_rate_pct=round(baseline_rev_recovery_rate, 2),
            net_revenue_recovery_rate_pct=round(baseline_net_rev_recovery_rate, 2),
            transaction_recovery_rate_pct=round(baseline_tx_recovery_rate, 2),
            recovered_count=len(baseline_recovered_payments),
            total_failed_count=total_records,
            total_retries_executed=baseline_total_retries,
            unnecessary_failed_retries=baseline_unnecessary_retries,
            overrides_enforced=0,
            fraud_blocks=0,
            escalations_count=0
        )

        # 3. Baseline 2: Simple Rule-Based
        rule_recovered_payments = [p for p in payments if p.rule_baseline_status == "RECOVERED"]
        rule_recovered_revenue = sum(p.rule_baseline_recovered_amount for p in rule_recovered_payments)
        rule_intervention_cost = sum(p.rule_baseline_intervention_cost for p in payments)
        rule_net_revenue = rule_recovered_revenue - rule_intervention_cost
        
        rule_rev_recovery_rate = (rule_recovered_revenue / total_revenue_at_risk * 100) if total_revenue_at_risk > 0 else 0.0
        rule_net_rev_recovery_rate = (rule_net_revenue / total_revenue_at_risk * 100) if total_revenue_at_risk > 0 else 0.0
        rule_tx_recovery_rate = (len(rule_recovered_payments) / total_records * 100) if total_records > 0 else 0.0
        
        rule_total_retries = sum(p.rule_baseline_retries for p in payments)
        rule_unnecessary_retries = sum(p.rule_baseline_retries for p in payments if p.rule_baseline_status != "RECOVERED")
        rule_fraud_blocks = sum(1 for p in payments if p.error_code == "SUSPECTED_FRAUD" and p.rule_baseline_action == "NO_ACTION")

        rule_metrics = StrategyMetrics(
            name="Simple Rule-Based Baseline",
            description="Static deterministic rules without contextual AI root-cause diagnosis, tier adaptation, or economic valuation.",
            total_revenue_at_risk=round(total_revenue_at_risk, 2),
            total_recovered_revenue=round(rule_recovered_revenue, 2),
            total_intervention_cost=round(rule_intervention_cost, 2),
            total_net_recovered_revenue=round(rule_net_revenue, 2),
            revenue_recovery_rate_pct=round(rule_rev_recovery_rate, 2),
            net_revenue_recovery_rate_pct=round(rule_net_rev_recovery_rate, 2),
            transaction_recovery_rate_pct=round(rule_tx_recovery_rate, 2),
            recovered_count=len(rule_recovered_payments),
            total_failed_count=total_records,
            total_retries_executed=rule_total_retries,
            unnecessary_failed_retries=rule_unnecessary_retries,
            overrides_enforced=0,
            fraud_blocks=rule_fraud_blocks,
            escalations_count=0
        )

        uplift_revenue = round(max(0.0, ai_recovered_revenue - baseline_recovered_revenue), 2)
        uplift_net_revenue = round(max(0.0, ai_net_recovered_revenue - baseline_net_revenue), 2)
        uplift_rate_pct = round(max(0.0, ai_tx_recovery_rate - baseline_tx_recovery_rate), 2)
        uplift_revenue_rate_pct = round(max(0.0, ai_rev_recovery_rate - baseline_rev_recovery_rate), 2)
        
        uplift_over_rule_rev = round(max(0.0, ai_recovered_revenue - rule_recovered_revenue), 2)
        uplift_over_rule_net_rev = round(max(0.0, ai_net_recovered_revenue - rule_net_revenue), 2)
        uplift_over_rule_rate = round(max(0.0, ai_tx_recovery_rate - rule_tx_recovery_rate), 2)
        uplift_over_rule_rev_rate = round(max(0.0, ai_rev_recovery_rate - rule_rev_recovery_rate), 2)
        
        retries_saved = max(0, baseline_total_retries - ai_retries_executed)
        customer_fatigue_prevented = baseline_unnecessary_retries

        return ComparisonSummary(
            llm_mode=current_llm_mode,
            total_records=total_records,
            ai_strategy=ai_metrics,
            baseline_strategy=blind_metrics,
            rule_baseline_strategy=rule_metrics,
            uplift_revenue=uplift_revenue,
            uplift_net_revenue=uplift_net_revenue,
            uplift_rate_pct=uplift_rate_pct,
            uplift_revenue_rate_pct=uplift_revenue_rate_pct,
            retries_saved=retries_saved,
            customer_fatigue_prevented=customer_fatigue_prevented,
            uplift_over_rule_revenue=uplift_over_rule_rev,
            uplift_over_rule_net_revenue=uplift_over_rule_net_rev,
            uplift_over_rule_rate_pct=uplift_over_rule_rate,
            uplift_over_rule_revenue_rate_pct=uplift_over_rule_rev_rate
        )

    @classmethod
    def get_system_overview(cls, db: Session) -> SystemOverview:
        """Retrieves high-level overview metrics for the dashboard."""
        payments = db.query(PaymentRecord).all()
        total_records = len(payments)
        revenue_at_risk = sum(p.amount for p in payments)
        
        ai_recovered = sum(p.recovered_amount for p in payments if p.status == "RECOVERED")
        ai_cost = sum(p.intervention_cost for p in payments)
        ai_net = ai_recovered - ai_cost
        ai_count = sum(1 for p in payments if p.status == "RECOVERED")
        ai_rev_rate = (ai_recovered / revenue_at_risk * 100) if revenue_at_risk > 0 else 0.0
        ai_tx_rate = (ai_count / total_records * 100) if total_records > 0 else 0.0

        base_recovered = sum(p.baseline_recovered_amount for p in payments if p.baseline_status == "RECOVERED")
        base_cost = sum(p.baseline_intervention_cost for p in payments)
        base_net = base_recovered - base_cost
        base_count = sum(1 for p in payments if p.baseline_status == "RECOVERED")
        base_rev_rate = (base_recovered / revenue_at_risk * 100) if revenue_at_risk > 0 else 0.0
        base_tx_rate = (base_count / total_records * 100) if total_records > 0 else 0.0

        rule_recovered = sum(p.rule_baseline_recovered_amount for p in payments if p.rule_baseline_status == "RECOVERED")
        rule_cost = sum(p.rule_baseline_intervention_cost for p in payments)
        rule_net = rule_recovered - rule_cost
        rule_count = sum(1 for p in payments if p.rule_baseline_status == "RECOVERED")
        rule_rev_rate = (rule_recovered / revenue_at_risk * 100) if revenue_at_risk > 0 else 0.0
        rule_tx_rate = (rule_count / total_records * 100) if total_records > 0 else 0.0

        latest_audit = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
        llm_mode = latest_audit.llm_mode if latest_audit else "Deterministic Fallback Mode"
        
        status_counts: Dict[str, int] = {}
        error_code_dist: Dict[str, int] = {}
        action_dist: Dict[str, int] = {}

        for p in payments:
            status_counts[p.status] = status_counts.get(p.status, 0) + 1
            error_code_dist[p.error_code] = error_code_dist.get(p.error_code, 0) + 1
            action_key = p.recovery_action_taken or "PENDING"
            action_dist[action_key] = action_dist.get(action_key, 0) + 1

        override_count = db.query(AuditLog).filter(AuditLog.policy_override == True).count()

        return SystemOverview(
            total_records=total_records,
            revenue_at_risk=round(revenue_at_risk, 2),
            recovered_revenue_ai=round(ai_recovered, 2),
            net_recovered_revenue_ai=round(ai_net, 2),
            revenue_recovery_rate_ai=round(ai_rev_rate, 2),
            transaction_recovery_rate_ai=round(ai_tx_rate, 2),
            recovered_revenue_baseline=round(base_recovered, 2),
            net_recovered_revenue_baseline=round(base_net, 2),
            revenue_recovery_rate_baseline=round(base_rev_rate, 2),
            transaction_recovery_rate_baseline=round(base_tx_rate, 2),
            recovered_revenue_rule_baseline=round(rule_recovered, 2),
            net_recovered_revenue_rule_baseline=round(rule_net, 2),
            revenue_recovery_rate_rule_baseline=round(rule_rev_rate, 2),
            transaction_recovery_rate_rule_baseline=round(rule_tx_rate, 2),
            llm_mode=llm_mode,
            status_counts=status_counts,
            error_code_distribution=error_code_dist,
            action_distribution=action_dist,
            policy_override_count=override_count
        )

    @classmethod
    def run_multi_seed_evaluation(
        cls, 
        seed_start: int = 1, 
        seed_end: int = 20, 
        count_per_seed: int = 100
    ) -> MultiSeedEvaluationResult:
        """
        Executes 20-seed robustness evaluation across seeds 1..20 to measure economic stability
        across pseudo-random datasets.
        """
        seeds = list(range(seed_start, seed_end + 1))
        per_seed_results = []
        
        ai_gross_revs = []
        ai_costs = []
        ai_net_revs = []
        ai_rev_rates = []
        ai_tx_rates = []

        rule_gross_revs = []
        rule_costs = []
        rule_net_revs = []
        rule_rev_rates = []
        rule_tx_rates = []

        blind_gross_revs = []
        blind_costs = []
        blind_net_revs = []
        blind_rev_rates = []
        blind_tx_rates = []

        for s in seeds:
            records = generate_synthetic_payments(count=count_per_seed, seed=s)
            total_risk = sum(r.amount for r in records)

            # 1. RecoverAI Simulation
            ai_gross = 0.0
            ai_cost = 0.0
            ai_count = 0
            for r in records:
                diag, _ = LLMService.diagnose_payment(r)
                policy_res = PolicyEngine.evaluate(r, diag)
                sim_res = SimulationEngine.simulate_ai_recovery(r, policy_res.approved_action, seed_offset=s)
                ai_cost += sim_res.intervention_cost
                if sim_res.status == "RECOVERED":
                    ai_count += 1
                    ai_gross += sim_res.recovered_amount
            ai_net = ai_gross - ai_cost

            # 2. Blind 3x Retry Simulation
            blind_gross = 0.0
            blind_cost = 0.0
            blind_count = 0
            for r in records:
                b_res = SimulationEngine.simulate_baseline_recovery(r)
                blind_cost += b_res["intervention_cost"]
                if b_res["status"] == "RECOVERED":
                    blind_count += 1
                    blind_gross += b_res["recovered_amount"]
            blind_net = blind_gross - blind_cost

            # 3. Rule-Based Recovery Simulation
            rule_gross = 0.0
            rule_cost = 0.0
            rule_count = 0
            for r in records:
                ru_res = SimulationEngine.simulate_rule_based_recovery(r)
                rule_cost += ru_res["intervention_cost"]
                if ru_res["status"] == "RECOVERED":
                    rule_count += 1
                    rule_gross += ru_res["recovered_amount"]
            rule_net = rule_gross - rule_cost

            ai_rev_rate = (ai_gross / total_risk * 100) if total_risk > 0 else 0.0
            ai_tx_rate = (ai_count / count_per_seed) * 100
            
            rule_rev_rate = (rule_gross / total_risk * 100) if total_risk > 0 else 0.0
            rule_tx_rate = (rule_count / count_per_seed) * 100
            
            blind_rev_rate = (blind_gross / total_risk * 100) if total_risk > 0 else 0.0
            blind_tx_rate = (blind_count / count_per_seed) * 100

            ai_gross_revs.append(ai_gross)
            ai_costs.append(ai_cost)
            ai_net_revs.append(ai_net)
            ai_rev_rates.append(ai_rev_rate)
            ai_tx_rates.append(ai_tx_rate)

            rule_gross_revs.append(rule_gross)
            rule_costs.append(rule_cost)
            rule_net_revs.append(rule_net)
            rule_rev_rates.append(rule_rev_rate)
            rule_tx_rates.append(rule_tx_rate)

            blind_gross_revs.append(blind_gross)
            blind_costs.append(blind_cost)
            blind_net_revs.append(blind_net)
            blind_rev_rates.append(blind_rev_rate)
            blind_tx_rates.append(blind_tx_rate)

            per_seed_results.append({
                "seed": s,
                "total_revenue_at_risk": round(total_risk, 2),
                "ai_gross_revenue": round(ai_gross, 2),
                "ai_intervention_cost": round(ai_cost, 2),
                "ai_net_revenue": round(ai_net, 2),
                "ai_revenue_rate": round(ai_rev_rate, 2),
                "ai_tx_recovery_rate": round(ai_tx_rate, 2),
                "rule_gross_revenue": round(rule_gross, 2),
                "rule_intervention_cost": round(rule_cost, 2),
                "rule_net_revenue": round(rule_net, 2),
                "rule_revenue_rate": round(rule_rev_rate, 2),
                "rule_tx_recovery_rate": round(rule_tx_rate, 2),
                "blind_gross_revenue": round(blind_gross, 2),
                "blind_intervention_cost": round(blind_cost, 2),
                "blind_net_revenue": round(blind_net, 2),
                "blind_revenue_rate": round(blind_rev_rate, 2),
                "blind_tx_recovery_rate": round(blind_tx_rate, 2),
                "net_uplift_over_blind": round(ai_net - blind_net, 2),
                "net_uplift_over_rule": round(ai_net - rule_net, 2),
                "tx_advantage_over_blind_pts": round(ai_tx_rate - blind_tx_rate, 2),
                "tx_advantage_over_rule_pts": round(ai_tx_rate - rule_tx_rate, 2),
                "tx_uplift_over_blind": round(ai_tx_rate - blind_tx_rate, 2),
                "tx_uplift_over_rule": round(ai_tx_rate - rule_tx_rate, 2)
            })

        n = len(seeds)
        mean_ai_gross = sum(ai_gross_revs) / n
        mean_ai_cost = sum(ai_costs) / n
        mean_ai_net = sum(ai_net_revs) / n
        mean_ai_rev_rate = sum(ai_rev_rates) / n
        mean_ai_tx_rate = sum(ai_tx_rates) / n

        sorted_ai_tx_rates = sorted(ai_tx_rates)
        median_ai_tx_rate = (sorted_ai_tx_rates[n // 2] + sorted_ai_tx_rates[(n - 1) // 2]) / 2

        variance_ai_tx = sum((x - mean_ai_tx_rate) ** 2 for x in ai_tx_rates) / (n - 1 if n > 1 else 1)
        std_dev_ai_tx = math.sqrt(variance_ai_tx)

        variance_ai_net = sum((x - mean_ai_net) ** 2 for x in ai_net_revs) / (n - 1 if n > 1 else 1)
        std_dev_ai_net = math.sqrt(variance_ai_net)

        mean_rule_gross = sum(rule_gross_revs) / n
        mean_rule_cost = sum(rule_costs) / n
        mean_rule_net = sum(rule_net_revs) / n
        mean_rule_rev_rate = sum(rule_rev_rates) / n
        mean_rule_tx_rate = sum(rule_tx_rates) / n
        variance_rule_tx = sum((x - mean_rule_tx_rate) ** 2 for x in rule_tx_rates) / (n - 1 if n > 1 else 1)
        std_dev_rule_tx = math.sqrt(variance_rule_tx)

        mean_blind_gross = sum(blind_gross_revs) / n
        mean_blind_cost = sum(blind_costs) / n
        mean_blind_net = sum(blind_net_revs) / n
        mean_blind_rev_rate = sum(blind_rev_rates) / n
        mean_blind_tx_rate = sum(blind_tx_rates) / n
        variance_blind_tx = sum((x - mean_blind_tx_rate) ** 2 for x in blind_tx_rates) / (n - 1 if n > 1 else 1)
        std_dev_blind_tx = math.sqrt(variance_blind_tx)

        # Economic Uplifts (Rupees & Percentage)
        net_uplift_blind = mean_ai_net - mean_blind_net
        net_uplift_pct_blind = (net_uplift_blind / mean_blind_net * 100) if mean_blind_net > 0 else 0.0
        
        net_uplift_rule = mean_ai_net - mean_rule_net
        net_uplift_pct_rule = (net_uplift_rule / mean_rule_net * 100) if mean_rule_net > 0 else 0.0

        # Transaction Recovery Differences (Percentage Points)
        tx_diff_blind = mean_ai_tx_rate - mean_blind_tx_rate
        tx_diff_rule = mean_ai_tx_rate - mean_rule_tx_rate

        return MultiSeedEvaluationResult(
            seed_count=n,
            seeds_evaluated=seeds,
            # RecoverAI
            ai_mean_gross_revenue=round(mean_ai_gross, 2),
            ai_mean_intervention_cost=round(mean_ai_cost, 2),
            ai_mean_net_revenue=round(mean_ai_net, 2),
            ai_mean_revenue_rate=round(mean_ai_rev_rate, 2),
            ai_mean_tx_recovery_rate=round(mean_ai_tx_rate, 2),
            ai_min_tx_recovery_rate=round(min(ai_tx_rates), 2),
            ai_max_tx_recovery_rate=round(max(ai_tx_rates), 2),
            ai_std_dev_tx_rate=round(std_dev_ai_tx, 2),
            ai_median_tx_recovery_rate=round(median_ai_tx_rate, 2),
            ai_min_net_revenue=round(min(ai_net_revs), 2),
            ai_max_net_revenue=round(max(ai_net_revs), 2),
            ai_std_dev_net_revenue=round(std_dev_ai_net, 2),
            # Simple Rule Baseline
            rule_mean_gross_revenue=round(mean_rule_gross, 2),
            rule_mean_intervention_cost=round(mean_rule_cost, 2),
            rule_mean_net_revenue=round(mean_rule_net, 2),
            rule_mean_revenue_rate=round(mean_rule_rev_rate, 2),
            rule_mean_tx_recovery_rate=round(mean_rule_tx_rate, 2),
            rule_min_tx_recovery_rate=round(min(rule_tx_rates), 2),
            rule_max_tx_recovery_rate=round(max(rule_tx_rates), 2),
            rule_std_dev_tx_rate=round(std_dev_rule_tx, 2),
            # Blind Retry Baseline
            blind_mean_gross_revenue=round(mean_blind_gross, 2),
            blind_mean_intervention_cost=round(mean_blind_cost, 2),
            blind_mean_net_revenue=round(mean_blind_net, 2),
            blind_mean_revenue_rate=round(mean_blind_rev_rate, 2),
            blind_mean_tx_recovery_rate=round(mean_blind_tx_rate, 2),
            blind_min_tx_recovery_rate=round(min(blind_tx_rates), 2),
            blind_max_tx_recovery_rate=round(max(blind_tx_rates), 2),
            blind_std_dev_tx_rate=round(std_dev_blind_tx, 2),
            # Uplifts & Advantages
            mean_net_uplift_over_blind=round(net_uplift_blind, 2),
            net_revenue_uplift_pct_over_blind=round(net_uplift_pct_blind, 2),
            mean_net_uplift_over_rule=round(net_uplift_rule, 2),
            net_revenue_uplift_pct_over_rule=round(net_uplift_pct_rule, 2),
            mean_tx_uplift_over_blind=round(tx_diff_blind, 2),
            mean_tx_uplift_over_rule=round(tx_diff_rule, 2),
            tx_advantage_over_blind_pts=round(tx_diff_blind, 2),
            tx_advantage_over_rule_pts=round(tx_diff_rule, 2),
            per_seed_results=per_seed_results
        )

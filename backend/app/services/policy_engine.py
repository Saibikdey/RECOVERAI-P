from typing import List
from app.config import settings
from app.schemas import RecoveryActionEnum, LLMDiagnosisOutput, PolicyEvaluationResult
from app.models import PaymentRecord

ALLOWED_ACTIONS = {
    RecoveryActionEnum.RETRY,
    RecoveryActionEnum.ALTERNATE_PAYMENT,
    RecoveryActionEnum.REMINDER,
    RecoveryActionEnum.ESCALATE,
    RecoveryActionEnum.NO_ACTION,
}

class PolicyEngine:
    """
    Deterministic Policy Guardrail Engine.
    
    CRITICAL INVARIANT:
    The Policy Engine has SOLE and FINAL authority over recovery decisions.
    The LLM provides an advisory recommendation which is strictly validated,
    sanitized, and overridden if any safety guardrail or threshold is violated.
    """

    @classmethod
    def evaluate(cls, payment: PaymentRecord, diagnosis: LLMDiagnosisOutput) -> PolicyEvaluationResult:
        recommended = diagnosis.recommended_action
        applied_rules: List[str] = []
        is_overridden = False
        override_reason = None
        approved_action = recommended

        # Guardrail 0: Action Whitelist Verification
        if recommended not in ALLOWED_ACTIONS:
            is_overridden = True
            approved_action = RecoveryActionEnum.ESCALATE
            override_reason = f"Security Violation: LLM produced unauthorized action '{recommended}'. Overriding to ESCALATE."
            applied_rules.append("RULE_UNAUTHORIZED_ACTION_BLOCK")
            return PolicyEvaluationResult(
                recommended_action=recommended,
                approved_action=approved_action,
                is_overridden=is_overridden,
                override_reason=override_reason,
                applied_rules=applied_rules,
                is_safe=False
            )
        applied_rules.append("RULE_ACTION_WHITELIST_VALIDATED")

        # Guardrail 1: Fraud & Security Safety Guard
        if payment.error_code == "SUSPECTED_FRAUD":
            if recommended in [RecoveryActionEnum.RETRY, RecoveryActionEnum.REMINDER]:
                is_overridden = True
                approved_action = RecoveryActionEnum.NO_ACTION
                override_reason = "Fraud Safety Guard: Retries and reminders are strictly prohibited on suspected fraud to prevent chargeback loss."
                applied_rules.append("RULE_FRAUD_ZERO_TOLERANCE_OVERRIDE")
            else:
                applied_rules.append("RULE_FRAUD_SAFE_ACTION_CONFIRMED")

        # Guardrail 2: Permanent Failure / Expired Card Guard
        elif payment.error_code == "CARD_EXPIRED":
            if approved_action == RecoveryActionEnum.RETRY:
                is_overridden = True
                approved_action = RecoveryActionEnum.ALTERNATE_PAYMENT
                override_reason = "Permanent Error Guard: Re-attempting an expired card is guaranteed to fail. Switched to ALTERNATE_PAYMENT."
                applied_rules.append("RULE_CARD_EXPIRED_NO_RETRY")
            else:
                applied_rules.append("RULE_CARD_EXPIRED_COMPLIANT")

        # Guardrail 3: Maximum Retries & Velocity Guard
        if approved_action == RecoveryActionEnum.RETRY and payment.retry_count >= settings.MAX_RETRIES:
            is_overridden = True
            if payment.customer_tier in ["VIP", "ENTERPRISE"] or payment.amount >= settings.HIGH_VALUE_THRESHOLD_INR:
                approved_action = RecoveryActionEnum.ESCALATE
                override_reason = f"Max Retries Exhausted ({payment.retry_count}/{settings.MAX_RETRIES}): High-value customer escalated to priority desk."
            else:
                approved_action = RecoveryActionEnum.ALTERNATE_PAYMENT
                override_reason = f"Max Retries Exhausted ({payment.retry_count}/{settings.MAX_RETRIES}): Switched to alternate payment request."
            applied_rules.append("RULE_MAX_RETRIES_LIMIT_ENFORCED")
        else:
            applied_rules.append(f"RULE_RETRY_BUDGET_OK ({payment.retry_count}/{settings.MAX_RETRIES})")

        # Guardrail 4: Confidence Threshold Guard
        if not is_overridden and diagnosis.confidence < settings.CONFIDENCE_THRESHOLD:
            if approved_action not in [RecoveryActionEnum.ESCALATE, RecoveryActionEnum.NO_ACTION]:
                is_overridden = True
                approved_action = RecoveryActionEnum.ESCALATE
                override_reason = f"Confidence Guard: LLM confidence ({diagnosis.confidence:.2f}) is below threshold ({settings.CONFIDENCE_THRESHOLD:.2f}). Escalated for human review."
                applied_rules.append("RULE_CONFIDENCE_THRESHOLD_OVERRIDE")
            else:
                applied_rules.append("RULE_LOW_CONFIDENCE_SAFE_HANDOFF")
        else:
            applied_rules.append(f"RULE_CONFIDENCE_ACCEPTABLE ({diagnosis.confidence:.2f} >= {settings.CONFIDENCE_THRESHOLD:.2f})")

        # Guardrail 5: High-Value & VIP Customer Escalation Guard
        if not is_overridden and (payment.amount >= settings.HIGH_VALUE_THRESHOLD_INR or payment.customer_tier in ["VIP", "ENTERPRISE"]):
            if payment.error_code in ["LIMIT_EXCEEDED", "DO_NOT_HONOR"] and approved_action == RecoveryActionEnum.RETRY:
                is_overridden = True
                approved_action = RecoveryActionEnum.ESCALATE
                override_reason = f"High-Value Guard: Large transaction (₹{payment.amount:,.2f}, Tier: {payment.customer_tier}) with decline '{payment.error_code}' routed to relationship manager."
                applied_rules.append("RULE_HIGH_VALUE_VIP_ESCALATION")
            else:
                applied_rules.append("RULE_HIGH_VALUE_VERIFIED")

        return PolicyEvaluationResult(
            recommended_action=recommended,
            approved_action=approved_action,
            is_overridden=is_overridden,
            override_reason=override_reason,
            applied_rules=applied_rules,
            is_safe=True
        )

import hashlib
import random
from typing import Dict, Any, Tuple
from app.schemas import RecoveryActionEnum, SimulationOutcome
from app.models import PaymentRecord


def stable_seed(value: str) -> int:
    """
    Deterministic, process-independent seed derivation.

    Python's built-in hash() is randomized per-process for str objects
    (PYTHONHASHSEED), so it CANNOT be used for reproducible simulation
    outcomes across separate runs of the backend (e.g. server restarts,
    the CLI evaluator, or pytest). SHA-256 has no such randomization:
    the same input string always maps to the same integer, in any
    process, on any machine.
    """
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)

# Explicit synthetic simulation recovery probability matrix for AI-Assisted Strategy
SYNTHETIC_AI_SUCCESS_PROBABILITIES: Dict[Tuple[str, str], float] = {
    # (error_code, action) -> success probability under simulation assumptions
    ("BANK_SERVER_DOWN", RecoveryActionEnum.RETRY.value): 0.86,
    ("BANK_SERVER_DOWN", RecoveryActionEnum.ALTERNATE_PAYMENT.value): 0.72,
    ("BANK_SERVER_DOWN", RecoveryActionEnum.ESCALATE.value): 0.65,
    ("BANK_SERVER_DOWN", RecoveryActionEnum.REMINDER.value): 0.30,
    ("BANK_SERVER_DOWN", RecoveryActionEnum.NO_ACTION.value): 0.0,

    ("NETWORK_TIMEOUT", RecoveryActionEnum.RETRY.value): 0.88,
    ("NETWORK_TIMEOUT", RecoveryActionEnum.ALTERNATE_PAYMENT.value): 0.75,
    ("NETWORK_TIMEOUT", RecoveryActionEnum.ESCALATE.value): 0.65,
    ("NETWORK_TIMEOUT", RecoveryActionEnum.REMINDER.value): 0.35,
    ("NETWORK_TIMEOUT", RecoveryActionEnum.NO_ACTION.value): 0.0,

    ("CARD_EXPIRED", RecoveryActionEnum.RETRY.value): 0.00, # Blind retry on expired card is guaranteed to fail
    ("CARD_EXPIRED", RecoveryActionEnum.ALTERNATE_PAYMENT.value): 0.84,
    ("CARD_EXPIRED", RecoveryActionEnum.REMINDER.value): 0.52,
    ("CARD_EXPIRED", RecoveryActionEnum.ESCALATE.value): 0.70,
    ("CARD_EXPIRED", RecoveryActionEnum.NO_ACTION.value): 0.0,

    ("INSUFFICIENT_FUNDS", RecoveryActionEnum.REMINDER.value): 0.78,
    ("INSUFFICIENT_FUNDS", RecoveryActionEnum.ALTERNATE_PAYMENT.value): 0.71,
    ("INSUFFICIENT_FUNDS", RecoveryActionEnum.ESCALATE.value): 0.64,
    ("INSUFFICIENT_FUNDS", RecoveryActionEnum.RETRY.value): 0.18,
    ("INSUFFICIENT_FUNDS", RecoveryActionEnum.NO_ACTION.value): 0.0,

    ("AUTHENTICATION_FAILED_3DS", RecoveryActionEnum.REMINDER.value): 0.82,
    ("AUTHENTICATION_FAILED_3DS", RecoveryActionEnum.ALTERNATE_PAYMENT.value): 0.68,
    ("AUTHENTICATION_FAILED_3DS", RecoveryActionEnum.ESCALATE.value): 0.60,
    ("AUTHENTICATION_FAILED_3DS", RecoveryActionEnum.RETRY.value): 0.22,
    ("AUTHENTICATION_FAILED_3DS", RecoveryActionEnum.NO_ACTION.value): 0.0,

    ("LIMIT_EXCEEDED", RecoveryActionEnum.ALTERNATE_PAYMENT.value): 0.80,
    ("LIMIT_EXCEEDED", RecoveryActionEnum.ESCALATE.value): 0.76,
    ("LIMIT_EXCEEDED", RecoveryActionEnum.REMINDER.value): 0.32,
    ("LIMIT_EXCEEDED", RecoveryActionEnum.RETRY.value): 0.05,
    ("LIMIT_EXCEEDED", RecoveryActionEnum.NO_ACTION.value): 0.0,

    ("SUSPECTED_FRAUD", RecoveryActionEnum.NO_ACTION.value): 1.00, # 100% successful block of fraudulent transaction
    ("SUSPECTED_FRAUD", RecoveryActionEnum.ESCALATE.value): 1.00,
    ("SUSPECTED_FRAUD", RecoveryActionEnum.RETRY.value): 0.00,
    ("SUSPECTED_FRAUD", RecoveryActionEnum.REMINDER.value): 0.00,
    ("SUSPECTED_FRAUD", RecoveryActionEnum.ALTERNATE_PAYMENT.value): 0.00,

    ("DO_NOT_HONOR", RecoveryActionEnum.ESCALATE.value): 0.68,
    ("DO_NOT_HONOR", RecoveryActionEnum.ALTERNATE_PAYMENT.value): 0.70,
    ("DO_NOT_HONOR", RecoveryActionEnum.REMINDER.value): 0.30,
    ("DO_NOT_HONOR", RecoveryActionEnum.RETRY.value): 0.12,
    ("DO_NOT_HONOR", RecoveryActionEnum.NO_ACTION.value): 0.0,
}

# Baseline 1: Naive Blind 3x Retry probability
BASELINE_BLIND_RETRY_PROBABILITIES: Dict[str, float] = {
    "BANK_SERVER_DOWN": 0.42,
    "NETWORK_TIMEOUT": 0.45,
    "CARD_EXPIRED": 0.00, # Retrying expired cards 3 times always fails
    "INSUFFICIENT_FUNDS": 0.16,
    "AUTHENTICATION_FAILED_3DS": 0.12,
    "LIMIT_EXCEEDED": 0.04,
    "SUSPECTED_FRAUD": 0.00,
    "DO_NOT_HONOR": 0.10,
}

# Baseline 2: Simple Static Rule-Based Action Mapping and Base Probabilities
RULE_BASED_ACTION_MAP: Dict[str, str] = {
    "BANK_SERVER_DOWN": RecoveryActionEnum.RETRY.value,
    "NETWORK_TIMEOUT": RecoveryActionEnum.RETRY.value,
    "CARD_EXPIRED": RecoveryActionEnum.ALTERNATE_PAYMENT.value,
    "INSUFFICIENT_FUNDS": RecoveryActionEnum.REMINDER.value,
    "AUTHENTICATION_FAILED_3DS": RecoveryActionEnum.REMINDER.value,
    "LIMIT_EXCEEDED": RecoveryActionEnum.ALTERNATE_PAYMENT.value,
    "SUSPECTED_FRAUD": RecoveryActionEnum.NO_ACTION.value,
    "DO_NOT_HONOR": RecoveryActionEnum.RETRY.value,
}

RULE_BASED_SUCCESS_PROBABILITIES: Dict[str, float] = {
    "BANK_SERVER_DOWN": 0.70,
    "NETWORK_TIMEOUT": 0.72,
    "CARD_EXPIRED": 0.65,
    "INSUFFICIENT_FUNDS": 0.58,
    "AUTHENTICATION_FAILED_3DS": 0.62,
    "LIMIT_EXCEEDED": 0.55,
    "SUSPECTED_FRAUD": 1.00, # Blocked safely
    "DO_NOT_HONOR": 0.15,
}

class SimulationEngine:
    """
    Simulates recovery outcomes under clearly documented synthetic assumptions.
    """

    @classmethod
    def simulate_ai_recovery(
        cls, 
        payment: PaymentRecord, 
        approved_action: RecoveryActionEnum,
        seed_offset: int = 0
    ) -> SimulationOutcome:
        """Simulates outcome of executing the policy-approved action for RecoverAI."""
        # Deterministic hash of transaction_id + action for repeatable simulation
        seed_val = stable_seed(f"{payment.transaction_id}_{approved_action.value}_{seed_offset}") % 10000
        rng = random.Random(seed_val)
        
        # Fraud protection special handling
        if payment.error_code == "SUSPECTED_FRAUD":
            if approved_action in [RecoveryActionEnum.NO_ACTION, RecoveryActionEnum.ESCALATE]:
                return SimulationOutcome(
                    status="RECOVERED", # Fraud successfully contained/blocked
                    simulated_probability=1.0,
                    recovered_amount=0.0, # Fraud blocked - ₹0 captured, fraud loss prevented
                    notes="Fraud safely contained. Zero chargeback liability incurred."
                )
            else:
                return SimulationOutcome(
                    status="FAILED",
                    simulated_probability=0.0,
                    recovered_amount=0.0,
                    notes="Fraudulent transaction failed."
                )
        
        # Look up synthetic probability
        prob = SYNTHETIC_AI_SUCCESS_PROBABILITIES.get((payment.error_code, approved_action.value), 0.40)
        
        # Customer tier bonus
        if payment.customer_tier == "VIP":
            prob = min(0.95, prob + 0.05)
        elif payment.customer_tier == "ENTERPRISE":
            prob = min(0.98, prob + 0.08)
            
        is_success = rng.random() < prob
        
        if is_success:
            return SimulationOutcome(
                status="RECOVERED",
                simulated_probability=round(prob, 2),
                recovered_amount=payment.amount,
                notes=f"Recovery successful via policy-approved action '{approved_action.value}' (simulated prob {prob:.0%})."
            )
        else:
            return SimulationOutcome(
                status="FAILED",
                simulated_probability=round(prob, 2),
                recovered_amount=0.0,
                notes=f"Recovery attempt with '{approved_action.value}' was unsuccessful."
            )

    @classmethod
    def simulate_baseline_recovery(cls, payment: PaymentRecord) -> Dict[str, Any]:
        """
        Baseline 1: Naive Blind Retry strategy (blind 3x retry on all payments).
        """
        seed_val = stable_seed(f"baseline_{payment.transaction_id}") % 10000
        rng = random.Random(seed_val)
        
        prob = BASELINE_BLIND_RETRY_PROBABILITIES.get(payment.error_code, 0.15)
        is_success = rng.random() < prob
        
        retries_executed = rng.randint(1, 2) if is_success else 3
        
        return {
            "status": "RECOVERED" if is_success else "PERMANENTLY_FAILED",
            "recovered_amount": payment.amount if is_success else 0.0,
            "retries_executed": retries_executed,
            "simulated_probability": round(prob, 2),
            "unnecessary_retries": retries_executed if not is_success else 0
        }

    @classmethod
    def simulate_rule_based_recovery(cls, payment: PaymentRecord) -> Dict[str, Any]:
        """
        Baseline 2: Simple Rule-Based Recovery.
        Applies static heuristics strictly from existing fields without AI contextual diagnosis.
        """
        seed_val = stable_seed(f"rule_base_{payment.transaction_id}") % 10000
        rng = random.Random(seed_val)
        
        # Static rule lookup
        action = RULE_BASED_ACTION_MAP.get(payment.error_code, RecoveryActionEnum.NO_ACTION.value)
        
        # Rule check: if retry count already >= 3 on transient error, stop retrying
        if action == RecoveryActionEnum.RETRY.value and payment.retry_count >= 3:
            action = RecoveryActionEnum.NO_ACTION.value
            return {
                "status": "FAILED",
                "action": action,
                "recovered_amount": 0.0,
                "retries_executed": 0,
                "simulated_probability": 0.0,
                "unnecessary_retries": 0
            }
            
        if payment.error_code == "SUSPECTED_FRAUD":
            return {
                "status": "RECOVERED", # Contained
                "action": RecoveryActionEnum.NO_ACTION.value,
                "recovered_amount": 0.0,
                "retries_executed": 0,
                "simulated_probability": 1.0,
                "unnecessary_retries": 0
            }

        prob = RULE_BASED_SUCCESS_PROBABILITIES.get(payment.error_code, 0.35)
        is_success = rng.random() < prob
        retries_executed = 1 if action == RecoveryActionEnum.RETRY.value else 0

        return {
            "status": "RECOVERED" if is_success else "FAILED",
            "action": action,
            "recovered_amount": payment.amount if is_success else 0.0,
            "retries_executed": retries_executed,
            "simulated_probability": round(prob, 2),
            "unnecessary_retries": retries_executed if not is_success else 0
        }

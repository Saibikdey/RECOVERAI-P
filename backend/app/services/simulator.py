import random
import hashlib
from typing import Dict, Any, Tuple, List, Optional
from app.schemas import RecoveryActionEnum, SimulationOutcome, ActionEconomics, EconomicEvaluationResult
from app.models import PaymentRecord

def stable_seed(value: str) -> int:
    """Produces a deterministic, platform-independent 32-bit integer seed using SHA-256."""
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)

# Synthetic Intervention Costs (INR) - Configurable Simulation Assumptions
INTERVENTION_COSTS: Dict[str, float] = {
    RecoveryActionEnum.RETRY.value: 20.0,             # Processing & gateway attempt fee
    RecoveryActionEnum.ALTERNATE_PAYMENT.value: 15.0,  # Dynamic checkout & instrument routing cost
    RecoveryActionEnum.REMINDER.value: 5.0,            # Contextual SMS / WhatsApp notification cost
    RecoveryActionEnum.ESCALATE.value: 150.0,          # Human relationship desk operational cost
    RecoveryActionEnum.NO_ACTION.value: 0.0,           # Zero cost
}

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
    Simulates recovery outcomes and economic net recovery under clearly documented synthetic assumptions.
    """

    @classmethod
    def get_action_probability(cls, payment: PaymentRecord, action: str) -> float:
        """Returns the synthetic recovery probability for a given payment and candidate action."""
        if payment.error_code == "SUSPECTED_FRAUD":
            return 1.0 if action in [RecoveryActionEnum.NO_ACTION.value, RecoveryActionEnum.ESCALATE.value] else 0.0
            
        prob = SYNTHETIC_AI_SUCCESS_PROBABILITIES.get((payment.error_code, action), 0.35)
        
        # Customer tier bonus
        if payment.customer_tier == "VIP":
            prob = min(0.95, prob + 0.05)
        elif payment.customer_tier == "ENTERPRISE":
            prob = min(0.98, prob + 0.08)
            
        # Penalty for previous retries
        if payment.retry_count > 0 and action == RecoveryActionEnum.RETRY.value:
            prob = max(0.02, prob - (payment.retry_count * 0.15))
            
        return round(prob, 2)

    @classmethod
    def evaluate_action_economics(
        cls, 
        payment: PaymentRecord, 
        policy_checks: Dict[str, Tuple[bool, Optional[str]]]
    ) -> EconomicEvaluationResult:
        """
        Calculates Expected Gross Recovery, Intervention Cost, and Expected Net Recovery
        for all 5 candidate actions to evaluate the economic trade-offs.
        """
        candidate_actions: List[ActionEconomics] = []
        
        for action_enum in RecoveryActionEnum:
            act_str = action_enum.value
            prob = cls.get_action_probability(payment, act_str)
            gross = round(prob * payment.amount, 2)
            cost = INTERVENTION_COSTS.get(act_str, 0.0)
            net = round(gross - cost, 2)
            
            is_eligible, policy_note = policy_checks.get(act_str, (True, None))
            
            candidate_actions.append(ActionEconomics(
                action=act_str,
                success_probability=prob,
                expected_gross_recovery=gross,
                intervention_cost=cost,
                expected_net_recovery=net,
                is_policy_eligible=is_eligible,
                policy_notes=policy_note
            ))

        # Find economically optimal allowed action
        allowed_actions = [a for a in candidate_actions if a.is_policy_eligible]
        if allowed_actions:
            optimal = max(allowed_actions, key=lambda a: a.expected_net_recovery)
            optimal_action = optimal.action
            optimal_net = optimal.expected_net_recovery
        else:
            optimal_action = RecoveryActionEnum.ESCALATE.value
            optimal_net = 0.0

        # Construct explanation
        why_text = f"Evaluated 5 candidate actions for ₹{payment.amount:,.2f} at-risk on {payment.error_code}. "
        if optimal_action == RecoveryActionEnum.NO_ACTION.value and payment.error_code == "SUSPECTED_FRAUD":
            why_text += "Zero-tolerance fraud protection mandates NO_ACTION to prevent chargeback loss."
        elif optimal_action != RecoveryActionEnum.RETRY.value and payment.retry_count >= 3:
            why_text += f"Retry budget exhausted ({payment.retry_count}/3). {optimal_action} delivers optimal net recovery of ₹{optimal_net:,.2f}."
        else:
            why_text += f"{optimal_action} yields highest expected net recovery of ₹{optimal_net:,.2f} (prob {candidate_actions[0].success_probability:.0%})."

        return EconomicEvaluationResult(
            recommended_action=candidate_actions[0].action,
            recommended_expected_net=candidate_actions[0].expected_net_recovery,
            optimal_economic_action=optimal_action,
            optimal_expected_net=optimal_net,
            why_this_action=why_text,
            candidate_actions=candidate_actions
        )

    @classmethod
    def simulate_ai_recovery(
        cls, 
        payment: PaymentRecord, 
        approved_action: RecoveryActionEnum,
        seed_offset: int = 0
    ) -> SimulationOutcome:
        """
        Simulates outcome of executing the policy-approved action for RecoverAI using stable SHA-256 seed.
        """
        # SHA-256 stable seed across Python processes
        seed_key = f"{payment.transaction_id}_{approved_action.value}_{seed_offset}"
        seed_val = stable_seed(seed_key) % 100000
        rng = random.Random(seed_val)
        
        intervention_cost = INTERVENTION_COSTS.get(approved_action.value, 0.0)
        
        # Fraud protection special handling
        if payment.error_code == "SUSPECTED_FRAUD":
            if approved_action in [RecoveryActionEnum.NO_ACTION, RecoveryActionEnum.ESCALATE]:
                return SimulationOutcome(
                    status="RECOVERED", # Fraud successfully contained/blocked
                    simulated_probability=1.0,
                    recovered_amount=0.0, # Fraud blocked - ₹0 captured, fraud loss prevented
                    intervention_cost=intervention_cost,
                    net_recovered_amount=round(-intervention_cost, 2),
                    notes="Fraud safely contained. Zero chargeback liability incurred."
                )
            else:
                return SimulationOutcome(
                    status="FAILED",
                    simulated_probability=0.0,
                    recovered_amount=0.0,
                    intervention_cost=intervention_cost,
                    net_recovered_amount=round(-intervention_cost, 2),
                    notes="Fraudulent transaction failed."
                )
        
        # Look up probability
        prob = cls.get_action_probability(payment, approved_action.value)
        is_success = rng.random() < prob
        
        if is_success:
            gross = payment.amount
            net = round(gross - intervention_cost, 2)
            return SimulationOutcome(
                status="RECOVERED",
                simulated_probability=prob,
                recovered_amount=gross,
                intervention_cost=intervention_cost,
                net_recovered_amount=net,
                notes=f"Recovery successful via action '{approved_action.value}' (prob {prob:.0%}, net ₹{net:,.2f})."
            )
        else:
            return SimulationOutcome(
                status="FAILED",
                simulated_probability=prob,
                recovered_amount=0.0,
                intervention_cost=intervention_cost,
                net_recovered_amount=round(-intervention_cost, 2),
                notes=f"Recovery attempt with '{approved_action.value}' was unsuccessful (cost ₹{intervention_cost:,.2f})."
            )

    @classmethod
    def simulate_baseline_recovery(cls, payment: PaymentRecord) -> Dict[str, Any]:
        """
        Baseline 1: Naive Blind Retry strategy (blind 3x retry on all payments).
        Uses stable SHA-256 seed.
        """
        seed_key = f"baseline_{payment.transaction_id}"
        seed_val = stable_seed(seed_key) % 100000
        rng = random.Random(seed_val)
        
        prob = BASELINE_BLIND_RETRY_PROBABILITIES.get(payment.error_code, 0.15)
        is_success = rng.random() < prob
        
        retries_executed = rng.randint(1, 2) if is_success else 3
        # Incur ₹20 retry fee for every blind attempt
        intervention_cost = retries_executed * INTERVENTION_COSTS[RecoveryActionEnum.RETRY.value]
        recovered_amount = payment.amount if is_success else 0.0
        net_recovered = round(recovered_amount - intervention_cost, 2)
        
        return {
            "status": "RECOVERED" if is_success else "PERMANENTLY_FAILED",
            "recovered_amount": recovered_amount,
            "intervention_cost": intervention_cost,
            "net_recovered_amount": net_recovered,
            "retries_executed": retries_executed,
            "simulated_probability": round(prob, 2),
            "unnecessary_retries": retries_executed if not is_success else 0
        }

    @classmethod
    def simulate_rule_based_recovery(cls, payment: PaymentRecord) -> Dict[str, Any]:
        """
        Baseline 2: Simple Rule-Based Recovery.
        Applies static heuristics strictly from existing fields without AI contextual diagnosis.
        Uses stable SHA-256 seed.
        """
        seed_key = f"rule_base_{payment.transaction_id}"
        seed_val = stable_seed(seed_key) % 100000
        rng = random.Random(seed_val)
        
        # Static rule lookup
        action = RULE_BASED_ACTION_MAP.get(payment.error_code, RecoveryActionEnum.NO_ACTION.value)
        intervention_cost = INTERVENTION_COSTS.get(action, 0.0)
        
        if action == RecoveryActionEnum.RETRY.value and payment.retry_count >= 3:
            action = RecoveryActionEnum.NO_ACTION.value
            return {
                "status": "FAILED",
                "action": action,
                "recovered_amount": 0.0,
                "intervention_cost": 0.0,
                "net_recovered_amount": 0.0,
                "retries_executed": 0,
                "simulated_probability": 0.0,
                "unnecessary_retries": 0
            }
            
        if payment.error_code == "SUSPECTED_FRAUD":
            return {
                "status": "RECOVERED", # Contained
                "action": RecoveryActionEnum.NO_ACTION.value,
                "recovered_amount": 0.0,
                "intervention_cost": 0.0,
                "net_recovered_amount": 0.0,
                "retries_executed": 0,
                "simulated_probability": 1.0,
                "unnecessary_retries": 0
            }

        prob = RULE_BASED_SUCCESS_PROBABILITIES.get(payment.error_code, 0.35)
        is_success = rng.random() < prob
        retries_executed = 1 if action == RecoveryActionEnum.RETRY.value else 0
        recovered_amount = payment.amount if is_success else 0.0
        net_recovered = round(recovered_amount - intervention_cost, 2)

        return {
            "status": "RECOVERED" if is_success else "FAILED",
            "action": action,
            "recovered_amount": recovered_amount,
            "intervention_cost": intervention_cost,
            "net_recovered_amount": net_recovered,
            "retries_executed": retries_executed,
            "simulated_probability": round(prob, 2),
            "unnecessary_retries": retries_executed if not is_success else 0
        }

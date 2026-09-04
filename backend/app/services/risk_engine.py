from typing import Dict, Any
from app.models import PaymentRecord

class RiskEngine:
    @staticmethod
    def evaluate_risk(payment: PaymentRecord) -> Dict[str, Any]:
        """Evaluates financial risk, customer value, and urgency for a failed payment."""
        urgency = "MEDIUM"
        recovery_feasibility = 0.5
        
        # High value evaluation
        is_high_value = payment.amount >= 50000.0 or payment.customer_tier in ["VIP", "ENTERPRISE"]
        
        # Error-specific feasibility
        if payment.error_code in ["BANK_SERVER_DOWN", "NETWORK_TIMEOUT"]:
            recovery_feasibility = 0.85
            urgency = "HIGH"
        elif payment.error_code in ["AUTHENTICATION_FAILED_3DS", "INSUFFICIENT_FUNDS"]:
            recovery_feasibility = 0.70
            urgency = "HIGH" if is_high_value else "MEDIUM"
        elif payment.error_code == "CARD_EXPIRED":
            recovery_feasibility = 0.65
            urgency = "LOW"
        elif payment.error_code == "LIMIT_EXCEEDED":
            recovery_feasibility = 0.50
            urgency = "HIGH" if is_high_value else "MEDIUM"
        elif payment.error_code == "SUSPECTED_FRAUD":
            recovery_feasibility = 0.05
            urgency = "CRITICAL"
        elif payment.error_code == "DO_NOT_HONOR":
            recovery_feasibility = 0.30
            urgency = "MEDIUM"
            
        # Penalty for previous failed retries
        if payment.retry_count > 0:
            recovery_feasibility = max(0.10, recovery_feasibility - (payment.retry_count * 0.15))

        return {
            "is_high_value": is_high_value,
            "urgency": urgency,
            "recovery_feasibility": round(recovery_feasibility, 2),
            "customer_fatigue_risk": "HIGH" if payment.retry_count >= 2 else "LOW",
        }

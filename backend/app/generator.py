import random
from datetime import datetime, timezone, timedelta
from typing import List
from app.models import PaymentRecord

ERROR_CATALOG = [
    {
        "code": "INSUFFICIENT_FUNDS",
        "message": "Account balance insufficient for transaction debit",
        "weight": 24,
        "typical_methods": ["UPI", "DEBIT_CARD", "NACH_MANDATE"],
        "min_amount": 1200.0,
        "max_amount": 35000.0
    },
    {
        "code": "CARD_EXPIRED",
        "message": "Card validity date is in the past",
        "weight": 14,
        "typical_methods": ["CREDIT_CARD", "DEBIT_CARD"],
        "min_amount": 1500.0,
        "max_amount": 28000.0
    },
    {
        "code": "BANK_SERVER_DOWN",
        "message": "Issuer bank core switch not responding (HTTP 504 / 91)",
        "weight": 18,
        "typical_methods": ["UPI", "NETBANKING", "CREDIT_CARD"],
        "min_amount": 2500.0,
        "max_amount": 75000.0
    },
    {
        "code": "NETWORK_TIMEOUT",
        "message": "Payment gateway timeout after processing request",
        "weight": 14,
        "typical_methods": ["UPI", "CREDIT_CARD", "NETBANKING"],
        "min_amount": 1000.0,
        "max_amount": 45000.0
    },
    {
        "code": "AUTHENTICATION_FAILED_3DS",
        "message": "Customer dropped out / failed OTP 3D-Secure verification",
        "weight": 14,
        "typical_methods": ["CREDIT_CARD", "DEBIT_CARD", "NETBANKING"],
        "min_amount": 3000.0,
        "max_amount": 55000.0
    },
    {
        "code": "LIMIT_EXCEEDED",
        "message": "Transaction amount exceeds per-day or single-transaction limit",
        "weight": 6,
        "typical_methods": ["UPI", "DEBIT_CARD"],
        "min_amount": 30000.0,
        "max_amount": 125000.0
    },
    {
        "code": "SUSPECTED_FRAUD",
        "message": "Security rule triggered: High velocity IP & device anomaly",
        "weight": 5,
        "typical_methods": ["CREDIT_CARD", "UPI"],
        "min_amount": 45000.0,
        "max_amount": 180000.0
    },
    {
        "code": "DO_NOT_HONOR",
        "message": "Card issuer declined transaction with generic code (05)",
        "weight": 5,
        "typical_methods": ["CREDIT_CARD", "DEBIT_CARD"],
        "min_amount": 4000.0,
        "max_amount": 60000.0
    }
]

FIRST_NAMES = ["Aarav", "Aditi", "Rohan", "Priya", "Vikram", "Neha", "Rahul", "Ananya", "Siddharth", "Pooja", "Karan", "Sneha", "Arjun", "Tanvi", "Amit", "Meera", "Varun", "Isha", "Ravi", "Divya"]
LAST_NAMES = ["Sharma", "Verma", "Patel", "Reddy", "Mehta", "Nair", "Gupta", "Deshmukh", "Singhania", "Iyer", "Rao", "Joshi", "Chopra", "Malhotra", "Bose", "Kulkarni"]

def generate_synthetic_payments(count: int = 100, seed: int = 42) -> List[PaymentRecord]:
    """Generates a realistic set of synthetic failed payment records."""
    rng = random.Random(seed)
    records = []
    
    # Pre-calculate distribution counts based on weights to reach exact total
    weights = [item["weight"] for item in ERROR_CATALOG]
    total_weight = sum(weights)
    
    # We will sample error scenarios
    for i in range(1, count + 1):
        err_item = rng.choices(ERROR_CATALOG, weights=weights, k=1)[0]
        
        # Pick customer details
        cust_first = rng.choice(FIRST_NAMES)
        cust_last = rng.choice(LAST_NAMES)
        customer_name = f"{cust_first} {cust_last}"
        customer_id = f"cust_{rng.randint(1001, 9999)}"
        
        # Customer tier distribution: 70% STANDARD, 20% VIP, 10% ENTERPRISE
        tier = rng.choices(["STANDARD", "VIP", "ENTERPRISE"], weights=[70, 20, 10], k=1)[0]
        
        # Payment method
        payment_method = rng.choice(err_item["typical_methods"])
        
        # Amount calculation
        base_amount = rng.uniform(err_item["min_amount"], err_item["max_amount"])
        if tier == "VIP":
            base_amount *= 1.3
        elif tier == "ENTERPRISE":
            base_amount *= 2.0
        amount = round(base_amount, 2)
        
        # Retry count: some already had 0, 1, 2, or 3 previous retries
        retry_count = rng.choices([0, 1, 2, 3], weights=[50, 30, 15, 5], k=1)[0]
        
        # Time generation (within past 48 hours)
        mins_ago = rng.randint(5, 2880)
        created_at = datetime.now(timezone.utc) - timedelta(minutes=mins_ago)
        last_attempt_mins_ago = max(1, mins_ago - rng.randint(0, 120))
        last_attempt_at = datetime.now(timezone.utc) - timedelta(minutes=last_attempt_mins_ago)
        
        # Initial risk assessment
        # Base risk from error type + amount + retries
        risk_score = 0.3
        if err_item["code"] == "SUSPECTED_FRAUD":
            risk_score = 0.95
        elif err_item["code"] == "LIMIT_EXCEEDED":
            risk_score = 0.75
        elif retry_count >= 2:
            risk_score += 0.25
        
        if amount > 50000:
            risk_score += 0.15
        
        risk_score = min(0.99, max(0.10, round(risk_score, 2)))
        
        if risk_score >= 0.85:
            risk_level = "CRITICAL"
        elif risk_score >= 0.65:
            risk_level = "HIGH"
        elif risk_score >= 0.40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        record = PaymentRecord(
            transaction_id=f"pay_fail_{i:03d}_{rng.randint(1000, 9999)}",
            customer_id=customer_id,
            customer_name=customer_name,
            customer_tier=tier,
            amount=amount,
            currency="INR",
            payment_method=payment_method,
            error_code=err_item["code"],
            error_message=err_item["message"],
            status="FAILED",
            retry_count=retry_count,
            last_attempt_at=last_attempt_at,
            created_at=created_at,
            risk_score=risk_score,
            risk_level=risk_level,
            recovery_action_taken=None,
            recovered_amount=0.0,
            baseline_status=None,
            baseline_retries=0,
            baseline_recovered_amount=0.0
        )
        records.append(record)
        
    return records

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class RecoveryActionEnum(str, Enum):
    RETRY = "RETRY"
    ALTERNATE_PAYMENT = "ALTERNATE_PAYMENT"
    REMINDER = "REMINDER"
    ESCALATE = "ESCALATE"
    NO_ACTION = "NO_ACTION"

class CustomerTierEnum(str, Enum):
    STANDARD = "STANDARD"
    VIP = "VIP"
    ENTERPRISE = "ENTERPRISE"

class RiskLevelEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class PaymentStatusEnum(str, Enum):
    FAILED = "FAILED"
    RECOVERED = "RECOVERED"
    PERMANENTLY_FAILED = "PERMANENTLY_FAILED"
    IN_PROGRESS = "IN_PROGRESS"

# Structured LLM Output Schema
class LLMDiagnosisOutput(BaseModel):
    root_cause_diagnosis: str = Field(description="Contextual root cause analysis of why the payment failed")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    recommended_action: RecoveryActionEnum = Field(description="Action recommendation: RETRY, ALTERNATE_PAYMENT, REMINDER, ESCALATE, or NO_ACTION")
    rationale: str = Field(description="Explanation of why this action is recommended")

# Policy Engine Evaluation Result
class PolicyEvaluationResult(BaseModel):
    recommended_action: str
    approved_action: RecoveryActionEnum
    is_overridden: bool
    override_reason: Optional[str] = None
    applied_rules: List[str]
    is_safe: bool = True

# Recovery Simulation Result
class SimulationOutcome(BaseModel):
    status: str # RECOVERED, FAILED, ESCALATED, BLOCKED, DUPLICATE_BLOCKED
    simulated_probability: float
    recovered_amount: float
    notes: str

# Full Pipeline Step-by-Step Response for Single Payment
class RecoveryPipelineResponse(BaseModel):
    payment_id: int
    transaction_id: str
    event_id: Optional[str] = None
    is_duplicate: bool = False
    message: Optional[str] = None
    llm_mode: str
    llm_diagnosis: LLMDiagnosisOutput
    policy_evaluation: PolicyEvaluationResult
    simulation_outcome: SimulationOutcome
    timestamp: datetime

# Payment Record Schemas
class PaymentRecordOut(BaseModel):
    id: int
    transaction_id: str
    customer_id: str
    customer_name: str
    customer_tier: str
    amount: float
    currency: str
    payment_method: str
    error_code: str
    error_message: str
    status: str
    retry_count: int
    last_attempt_at: datetime
    created_at: datetime
    risk_score: float
    risk_level: str
    
    # AI Recovery
    recovery_action_taken: Optional[str] = None
    recovered_amount: float = 0.0
    
    # Baseline 1: Blind Retries
    baseline_status: Optional[str] = None
    baseline_retries: int = 0
    baseline_recovered_amount: float = 0.0
    
    # Baseline 2: Rule-Based Recovery
    rule_baseline_status: Optional[str] = None
    rule_baseline_action: Optional[str] = None
    rule_baseline_retries: int = 0
    rule_baseline_recovered_amount: float = 0.0

    model_config = ConfigDict(from_attributes=True)

# Audit Log Schema
class AuditLogOut(BaseModel):
    id: int
    payment_id: int
    transaction_id: str
    event_id: Optional[str] = None
    duplicate_blocked: bool = False
    llm_mode: str
    llm_diagnosis: str
    llm_confidence: float
    llm_action_recommended: str
    policy_action_approved: str
    policy_override: bool
    policy_override_reason: Optional[str]
    simulation_status: str
    simulated_probability: float
    recovered_amount: float
    timestamp: datetime
    details_json: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# Metrics & Summary
class StrategyMetrics(BaseModel):
    name: str
    description: str
    total_revenue_at_risk: float
    total_recovered_revenue: float
    recovery_rate_pct: float
    recovered_count: int
    total_failed_count: int
    total_retries_executed: int
    unnecessary_failed_retries: int
    overrides_enforced: int = 0
    fraud_blocks: int = 0
    escalations_count: int = 0

class ComparisonSummary(BaseModel):
    assumption_disclaimer: str = "All recovery outcomes and rates are derived from SYNTHETIC SIMULATION ASSUMPTIONS based on payment error mechanics and action suitability."
    why_ai_statement: str = "AI performs contextual root-cause diagnosis and recommends an action; deterministic rules validate and authorize the action."
    llm_mode: str
    total_records: int
    
    # 3-Way Strategy Comparison
    ai_strategy: StrategyMetrics
    baseline_strategy: StrategyMetrics
    rule_baseline_strategy: Optional[StrategyMetrics] = None
    
    # Uplift vs Blind Baseline
    uplift_revenue: float
    uplift_rate_pct: float
    retries_saved: int
    customer_fatigue_prevented: int
    
    # Uplift vs Rule-Based Baseline
    uplift_over_rule_revenue: float = 0.0
    uplift_over_rule_rate_pct: float = 0.0

class MultiSeedEvaluationResult(BaseModel):
    assumption_disclaimer: str = "Multi-seed evaluation across synthetic pseudo-random datasets demonstrates consistent performance across variance."
    seed_count: int
    seeds_evaluated: List[int]
    
    # Aggregate Stats across seeds
    ai_mean_recovery_rate: float
    ai_min_recovery_rate: float
    ai_max_recovery_rate: float
    ai_mean_recovered_revenue: float
    
    blind_mean_recovery_rate: float
    blind_mean_recovered_revenue: float
    
    rule_mean_recovery_rate: float
    rule_mean_recovered_revenue: float
    
    mean_uplift_over_blind_rate: float
    mean_uplift_over_blind_revenue: float
    
    mean_uplift_over_rule_rate: float
    mean_uplift_over_rule_revenue: float
    
    std_dev_recovery_rate: float
    per_seed_results: List[Dict[str, Any]]

class SystemOverview(BaseModel):
    total_records: int
    revenue_at_risk: float
    recovered_revenue_ai: float
    recovery_rate_ai: float
    recovered_revenue_baseline: float
    recovery_rate_baseline: float
    recovered_revenue_rule_baseline: float = 0.0
    recovery_rate_rule_baseline: float = 0.0
    llm_mode: str
    status_counts: Dict[str, int]
    error_code_distribution: Dict[str, int]
    action_distribution: Dict[str, int]
    policy_override_count: int

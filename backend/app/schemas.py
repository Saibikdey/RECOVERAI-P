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

# Structured LLM Output Schema (Advisory Only)
class LLMDiagnosisOutput(BaseModel):
    root_cause_diagnosis: str = Field(description="Contextual root cause analysis of why the payment failed")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    recommended_action: RecoveryActionEnum = Field(description="Action recommendation: RETRY, ALTERNATE_PAYMENT, REMINDER, ESCALATE, or NO_ACTION")
    rationale: str = Field(description="Explanation of why this action is recommended")

# Economic Evaluation for Candidate Actions
class ActionEconomics(BaseModel):
    action: str
    success_probability: float
    expected_gross_recovery: float
    intervention_cost: float
    expected_net_recovery: float
    is_policy_eligible: bool
    policy_notes: Optional[str] = None

class EconomicEvaluationResult(BaseModel):
    recommended_action: str
    recommended_expected_net: float
    optimal_economic_action: str
    optimal_expected_net: float
    why_this_action: str
    candidate_actions: List[ActionEconomics]

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
    recovered_amount: float     # Gross revenue recovered
    intervention_cost: float    # Synthetic operational cost
    net_recovered_amount: float # Net = Gross - Cost
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
    economic_evaluation: Optional[EconomicEvaluationResult] = None
    policy_evaluation: PolicyEvaluationResult
    simulation_outcome: SimulationOutcome
    timestamp: datetime

# Payment Record Schema
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
    intervention_cost: float = 0.0
    net_recovered_amount: float = 0.0
    
    # Baseline 1: Blind Retries
    baseline_status: Optional[str] = None
    baseline_retries: int = 0
    baseline_recovered_amount: float = 0.0
    baseline_intervention_cost: float = 0.0
    baseline_net_recovered_amount: float = 0.0
    
    # Baseline 2: Rule-Based Recovery
    rule_baseline_status: Optional[str] = None
    rule_baseline_action: Optional[str] = None
    rule_baseline_retries: int = 0
    rule_baseline_recovered_amount: float = 0.0
    rule_baseline_intervention_cost: float = 0.0
    rule_baseline_net_recovered_amount: float = 0.0

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
    intervention_cost: float = 0.0
    net_recovered_amount: float = 0.0
    timestamp: datetime
    details_json: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# Metrics & Summary
class StrategyMetrics(BaseModel):
    name: str
    description: str
    total_revenue_at_risk: float
    total_recovered_revenue: float       # Gross
    total_intervention_cost: float       # Cost
    total_net_recovered_revenue: float   # Net = Gross - Cost
    revenue_recovery_rate_pct: float     # Gross Recovered / Revenue at Risk
    net_revenue_recovery_rate_pct: float # Net Recovered / Revenue at Risk
    transaction_recovery_rate_pct: float # Transactions Recovered / Total Count
    recovered_count: int
    total_failed_count: int
    total_retries_executed: int
    unnecessary_failed_retries: int
    overrides_enforced: int = 0
    fraud_blocks: int = 0
    escalations_count: int = 0

class ComparisonSummary(BaseModel):
    assumption_disclaimer: str = "All recovery outcomes, probabilities, and intervention costs are derived from SYNTHETIC SIMULATION ASSUMPTIONS."
    why_ai_statement: str = "AI performs contextual root-cause diagnosis and recommends an action; deterministic rules validate and authorize the action."
    llm_mode: str
    dataset_seed: int = 42
    total_records: int
    
    # 3-Way Strategy Comparison
    ai_strategy: StrategyMetrics
    baseline_strategy: StrategyMetrics
    rule_baseline_strategy: Optional[StrategyMetrics] = None
    
    # Uplift vs Blind Baseline
    uplift_revenue: float                # Gross revenue uplift
    uplift_net_revenue: float            # Net revenue uplift
    uplift_rate_pct: float               # Transaction recovery rate uplift
    uplift_revenue_rate_pct: float       # Revenue recovery rate uplift
    retries_saved: int
    customer_fatigue_prevented: int
    
    # Uplift vs Rule-Based Baseline
    uplift_over_rule_revenue: float      # Gross revenue uplift
    uplift_over_rule_net_revenue: float  # Net revenue uplift
    uplift_over_rule_rate_pct: float     # Transaction recovery rate uplift
    uplift_over_rule_revenue_rate_pct: float

class MultiSeedEvaluationResult(BaseModel):
    assumption_disclaimer: str = "20-seed robustness evaluation across synthetic pseudo-random datasets demonstrates consistent economic performance."
    seed_count: int
    seeds_evaluated: List[int]
    
    # RecoverAI (AI + Policy Engine)
    ai_mean_gross_revenue: float
    ai_mean_intervention_cost: float
    ai_mean_net_revenue: float
    ai_mean_revenue_rate: float
    ai_mean_tx_recovery_rate: float
    ai_min_tx_recovery_rate: float
    ai_max_tx_recovery_rate: float
    ai_std_dev_tx_rate: float
    ai_median_tx_recovery_rate: float
    ai_min_net_revenue: float = 0.0
    ai_max_net_revenue: float = 0.0
    ai_std_dev_net_revenue: float = 0.0
    
    # Simple Rule-Based Baseline
    rule_mean_gross_revenue: float
    rule_mean_intervention_cost: float
    rule_mean_net_revenue: float
    rule_mean_revenue_rate: float
    rule_mean_tx_recovery_rate: float
    rule_min_tx_recovery_rate: float = 0.0
    rule_max_tx_recovery_rate: float = 0.0
    rule_std_dev_tx_rate: float = 0.0
    
    # Naive Blind Retry Baseline
    blind_mean_gross_revenue: float
    blind_mean_intervention_cost: float
    blind_mean_net_revenue: float
    blind_mean_revenue_rate: float
    blind_mean_tx_recovery_rate: float
    blind_min_tx_recovery_rate: float = 0.0
    blind_max_tx_recovery_rate: float = 0.0
    blind_std_dev_tx_rate: float = 0.0
    
    # Economic Uplift vs Baselines (Rupee Amount & % Net Uplift)
    mean_net_uplift_over_blind: float
    net_revenue_uplift_pct_over_blind: float = 0.0
    mean_net_uplift_over_rule: float
    net_revenue_uplift_pct_over_rule: float = 0.0
    
    # Transaction Recovery Differences (Percentage Points)
    mean_tx_uplift_over_blind: float
    mean_tx_uplift_over_rule: float
    tx_advantage_over_blind_pts: float = 0.0
    tx_advantage_over_rule_pts: float = 0.0
    
    per_seed_results: List[Dict[str, Any]]

class SystemOverview(BaseModel):
    dataset_seed: int = 42
    total_records: int
    revenue_at_risk: float
    recovered_revenue_ai: float          # Gross
    net_recovered_revenue_ai: float      # Net
    revenue_recovery_rate_ai: float      # Gross / Risk
    transaction_recovery_rate_ai: float  # Count / Total
    
    recovered_revenue_baseline: float
    net_recovered_revenue_baseline: float
    revenue_recovery_rate_baseline: float
    transaction_recovery_rate_baseline: float
    
    recovered_revenue_rule_baseline: float = 0.0
    net_recovered_revenue_rule_baseline: float = 0.0
    revenue_recovery_rate_rule_baseline: float = 0.0
    transaction_recovery_rate_rule_baseline: float = 0.0
    
    llm_mode: str
    status_counts: Dict[str, int]
    error_code_distribution: Dict[str, int]
    action_distribution: Dict[str, int]
    policy_override_count: int

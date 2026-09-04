# RecoverAI System Architecture & Safety Design

> **Razorpay AI Buildathon 2026 — Track 03: AI Revenue Recovery Agent**

---

## 1. End-to-End System Architecture

```mermaid
flowchart TD
    subgraph Frontend_Layer ["Frontend Layer (React 18 + Vite + Tailwind CSS)"]
        UI_KPI["Executive KPI Dashboard"]
        UI_Comp["3-Way Comparative Analytics (Blind vs Rule vs RecoverAI)"]
        UI_Seed["20-Seed Robustness Evaluation View"]
        UI_Grid["100-Record Transaction Grid"]
        UI_Modal["Live 4-Stage Recovery Pipeline Modal (AI vs Policy Boundary)"]
        UI_Audit["Decision & Guardrail Audit Trail (with Duplicate Tracking)"]
    end

    subgraph API_Layer ["FastAPI Application Layer (REST API)"]
        API_Payments["/api/payments (Dataset, Reset, Filters)"]
        API_Recovery["/api/recovery (Diagnose, Batch, Baseline, Rule-Baseline)"]
        API_MultiSeed["/api/recovery/multi-seed-evaluation (20-Seed Engine)"]
        API_Audit["/api/audit (Audit Logs & Overrides)"]
        API_Analytics["/api/analytics (Overview KPIs)"]
    end

    subgraph Core_Engines ["Core Business & Safety Engines"]
        IDEMP["Idempotency Engine (Duplicate Request Protection)"]
        ORCH["Recovery Orchestrator"]
        RISK["Risk Engine (Feasibility & Value)"]
        
        subgraph AI_Advisory ["AI Advisory Sub-System"]
            LLM["LLM Diagnostic Service\n(Root-Cause, Confidence, Recommendation)\n[ADVISORY ONLY]"]
        end

        subgraph Policy_Authority ["Deterministic Policy Engine"]
            PE["POLICY ENGINE (THE FINAL & SOLE AUTHORITY)\n• Action Whitelist Enforcement\n• Max Retries Limit (Attempts >= 3)\n• Confidence Guard (< 0.65)\n• Fraud Zero-Tolerance Protection\n• Expired Card Auto-Routing\n• High-Value & VIP Account Escalation"]
        end

        SIM["Simulation & Analytics Engine\n(Synthetic Outcome Determination for 3 Strategies)"]
    end

    subgraph Storage_Layer ["SQLite Storage Layer"]
        DB_Payments[("payment_records\n(100 Synthetic Payments)")]
        DB_Events[("processed_events\n(Idempotency Store)")]
        DB_Audit[("audit_logs\n(Immutable Decision Trail)")]
    end

    Frontend_Layer <==>|HTTP / REST API| API_Layer
    API_Layer ==> ORCH
    ORCH --> IDEMP
    IDEMP --> DB_Events
    ORCH --> RISK
    ORCH --> LLM
    LLM -->|Advisory Recommendation| PE
    PE ==>|Approved & Validated Action| SIM
    SIM --> ORCH
    ORCH ==> DB_Payments
    ORCH ==> DB_Audit
```

---

## 2. Zero-Trust Authority Flow

```
LLM Diagnostic Service              Deterministic Policy Engine               Outcome / Execution
   (ADVISORY ONLY)                     (FINAL AUTHORITY)                       (SIMULATION ONLY)

┌───────────────────────┐            ┌───────────────────────┐            ┌───────────────────────┐
│ • Root-Cause Analysis │            │ • Whitelist Validation│            │ • Simulated Recovery  │
│ • Confidence Score    │ ─────────> │ • Safety Guardrails   │ ─────────> │ • Net Revenue Calculation │
│ • Recommended Action  │            │ • Explicit Overrides  │            │ • Immutable Audit Log │
└───────────────────────┘            └───────────────────────┘            └───────────────────────┘
  *Zero financial state                *Sole authorization                   *Synthetic outcomes
   modification power*                  decision maker*                       only*
```

> [!IMPORTANT]
> **Safety Rule**: The LLM is strictly an advisory diagnostic agent. It has **zero permission** to execute transactions or alter ledger state directly. Every recommendation must be approved or overridden by the deterministic Policy Engine before execution.

---

## 3. Policy Engine Guardrail Matrix

| Scenario | Trigger Condition | Policy Approved Action | Guardrail Rule & Audit Reason |
|---|---|---|---|
| **Idempotency Guard** | Duplicate `event_id` submission | `DUPLICATE_BLOCKED` | `RULE_IDEMPOTENCY_DUPLICATE_BLOCK`: Prevents duplicate executions. |
| **Unauthorized Action** | LLM outputs non-whitelisted string | `ESCALATE` | `RULE_UNAUTHORIZED_ACTION_BLOCK`: Blocks unauthorized proposals. |
| **Suspected Fraud** | `error_code == 'SUSPECTED_FRAUD'` | `NO_ACTION` | `RULE_FRAUD_ZERO_TOLERANCE`: Prohibits retries/reminders on fraud. |
| **Expired Instrument** | `error_code == 'CARD_EXPIRED'` | `ALTERNATE_PAYMENT` | `RULE_CARD_EXPIRED_NO_RETRY`: Retrying expired card guaranteed to fail. |
| **Max Retries Exceeded** | `retry_count >= 3` | `ALTERNATE_PAYMENT` / `ESCALATE` | `RULE_MAX_RETRIES_LIMIT_ENFORCED`: Prevents customer fatigue. |
| **Low Confidence** | `confidence < 0.65` | `ESCALATE` | `RULE_CONFIDENCE_THRESHOLD_OVERRIDE`: Routes to human verification. |
| **High-Value / VIP** | Amount $\ge$ ₹50,000 or VIP account | `ESCALATE` | `RULE_HIGH_VALUE_VIP_ESCALATION`: Priority desk handoff. |

---

## 4. 3-Way Comparative Evaluation Framework

To objectively quantify recovery performance and economic viability, RecoverAI implements a comprehensive 3-way evaluation framework:

> [!NOTE]
> **Synthetic Domain Assumptions Disclaimer**: All strategies are evaluated against a documented synthetic outcome model ([`simulator.py`](backend/app/services/simulator.py)). Outcomes, probabilities, and financial figures reflect controlled simulation performance, **not empirical live gateway data or real-world statistical significance**. The 20-seed robustness evaluation tests whether the comparative advantage holds across 20 distinct pseudo-random transaction mixes (2,000 transactions).

1. **Baseline 1: Naive Blind Retry**:
   - **Strategy**: Blind immediate 3x retries on all payment failures without root-cause diagnosis or safety filters.
   - **20-Seed Performance**: Mean Gross ₹7.05L | Mean Cost ₹5,387 | **Mean Net ₹7.00L** | Mean Rev Rate 18.90% | **Mean Tx Rate 20.75%** (±4.58%).
   - **Outcome**: Low recovery, heavy customer fatigue (228 wasted failures in Seed 42), and wasted intervention costs.

2. **Baseline 2: Simple Rule-Based Recovery**:
   - **Strategy**: Static deterministic mapping of error codes to recovery channels without customer tier, value, or channel context.
   - **20-Seed Performance**: Mean Gross ₹18.48L | Mean Cost ₹1,202 | **Mean Net ₹18.47L** | Mean Rev Rate 49.91% | **Mean Tx Rate 63.05%** (±4.37%).
   - **Outcome**: Improved over blind retries, but incapable of nuanced multi-variable reasoning for VIP accounts or ambiguous declines.

3. **RecoverAI (AI Contextual Diagnosis + Deterministic Policy Engine)**:
   - **Strategy**: LLM contextual root-cause reasoning combined with strict deterministic policy guardrails and economic optimization.
   - **20-Seed Performance**: Mean Gross ₹25.53L | Mean Cost ₹2,111 | **Mean Net ₹25.51L** (±₹2.62L) | Mean Rev Rate 68.62% | **Mean Tx Rate 82.15%** (±4.22%, range 74.0% – 89.0%).
   - **Comparative Advantage**:
     - **vs Simple Rule**: **+₹703,461.20 (+38.08% net revenue uplift)**, **+19.10 percentage points** transaction recovery advantage.
     - **vs Blind Retry**: **+₹1,851,006.58 (+264.55% net revenue uplift)**, **+61.40 percentage points** transaction recovery advantage.

---

## 5. Directory Structure

```
recoverai/
├── backend/
│   ├── app/
│   │   ├── config.py              # Configuration & LLM provider detection
│   │   ├── database.py            # SQLite session management
│   │   ├── models.py              # PaymentRecord, ProcessedEvent, & AuditLog models
│   │   ├── schemas.py             # Pydantic schemas, 3-way metrics, & multi-seed schemas
│   │   ├── generator.py           # Synthetic data generator (seed=42 for main demo)
│   │   ├── main.py                # FastAPI entrypoint, CORS, startup lifecycle
│   │   ├── services/
│   │   │   ├── risk_engine.py     # Revenue at risk & feasibility assessment
│   │   │   ├── llm_service.py     # LLM diagnostic service + deterministic fallback
│   │   │   ├── policy_engine.py   # FINAL AUTHORITY deterministic guardrails
│   │   │   ├── simulator.py       # 3-way strategy simulation engine & cost model
│   │   │   └── orchestrator.py    # Pipeline coordinator & multi-seed evaluation
│   │   └── routers/
│   │       ├── payments.py        # /api/payments endpoints (with idempotency reset)
│   │       ├── recovery.py        # /api/recovery endpoints (diagnose, batch, baselines)
│   │       ├── audit.py           # /api/audit endpoints (with duplicate tracking)
│   │       └── analytics.py       # /api/analytics endpoints
│   ├── scripts/
│   │   └── evaluate_seeds.py      # 20-seed robustness evaluation CLI script
│   ├── tests/
│   │   └── test_core.py           # 15 automated unit & integration tests
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx         # Status badge, 3 baseline trigger buttons
│   │   │   ├── KpiCards.jsx       # 5 financial KPI cards & simulation disclaimer
│   │   │   ├── ComparisonView.jsx # 3-way strategy comparison & 20-seed robustness drawer
│   │   │   ├── TransactionTable.jsx # 100-record grid with search/filters
│   │   │   ├── RecoveryModal.jsx  # Live 4-stage pipeline modal (AI vs Policy boundary)
│   │   │   ├── AuditTrail.jsx     # Filterable override & duplicate audit log
│   │   │   └── ArchitectureView.jsx # In-app architecture & safety inspector
│   │   ├── App.jsx                # Main application container
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── .env.example                   # Root environment template
├── .gitignore                     # Git ignore rules
├── README.md                      # Comprehensive project overview & demo guide
└── ARCHITECTURE.md                # System architecture & safety design document
```

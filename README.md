# RecoverAI

> **AI-Assisted Revenue Recovery Agent with Deterministic Safety Guardrails**  
> **Track**: Razorpay AI Buildathon 2026 — Track 03: AI Revenue Recovery

---

## 📌 Problem & Solution

### Problem
Failed digital payments are not all the same. Traditional payment recovery relies on rigid, blind retries that repeatedly trigger issuer declines, cause customer fatigue, and waste transaction fees on permanent errors (such as expired cards or daily limits).

### Solution
**RecoverAI** contextually diagnoses failed transactions using AI, recommends a tailored recovery intervention, and routes that recommendation through a deterministic Policy Engine before any recovery action is simulated.

---

## ⚠️ IMPORTANT: SIMULATION ONLY

> [!CAUTION]
> **This application is a strictly controlled synthetic simulation**:
> - **All payment records are 100% synthetic**.
> - **No real money is moved**, and **no real payment credentials** or live banking gateways are used.
> - Recovery outcomes, probabilities, and financial figures represent **Simulated Revenue Recovered** generated under documented synthetic domain assumptions.
> - Results are comparative research simulations, **not claims of real-world production performance**.
> - Pseudorandom seed `42` is used for **100% deterministic reproducibility** during live demos, accompanied by an automated **20-seed robustness evaluation** across 2,000 transactions.
> - The evaluation uses a synthetic outcome model with documented probability assumptions (see [`simulator.py`](backend/app/services/simulator.py)). Therefore, the comparison should be interpreted as a **controlled simulation of strategy performance**, not empirical evidence of real-world recovery rates. The 20-seed run tests whether the observed strategy difference **remains consistent across different synthetic transaction mixes** — it does not establish real-world statistical significance.
> - The AI **confidence score** is an internal decision signal used by the Policy Engine's confidence threshold guardrail; it is **not a calibrated real-world accuracy probability**.

---

## 💡 Why AI + Rules?

> **"AI performs contextual root-cause diagnosis and recommends an action; deterministic rules validate and authorize the action."**

- **Why AI?** Digital payment failures are multifaceted. The same error code (`DO_NOT_HONOR` or `LIMIT_EXCEEDED`) requires different handling depending on customer tier (VIP vs Standard), prior retry count, and transaction amount. AI provides contextual reasoning that static lookup tables cannot provide.
- **Why Deterministic Rules?** Financial systems require zero-trust safety. An LLM must **never** have autonomous authority to debit accounts or modify financial ledgers. The deterministic Policy Engine acts as the sole, unalterable final authority.

```
Payment Failure Event
         │
         ▼
┌──────────────────────────────────────────────┐
│       1. IDEMPOTENCY / EVENT GUARD           │
│  • Checks unique event_id                    │
│  • Blocks duplicate execution attempts       │
└──────────────────────┬───────────────────────┘
                       │ Valid New Event
                       ▼
┌──────────────────────────────────────────────┐
│        2. AI DIAGNOSTIC LAYER                │
│  • Contextual Root-Cause Analysis            │
│  • Confidence Score (0.0 to 1.0)             │
│  • Recommended Action (ADVISORY ONLY)        │
└──────────────────────┬───────────────────────┘
                       │ Advisory Proposal
                       ▼
┌──────────────────────────────────────────────┐
│     3. DETERMINISTIC POLICY ENGINE           │
│          (THE FINAL AUTHORITY)               │
│  • Action Whitelist Enforcement              │
│  • Max Retries Guard (Attempts >= 3)         │
│  • Confidence Threshold Guard (< 0.65)       │
│  • Fraud Zero-Tolerance Protection           │
│  • Expired Instrument Alternative Routing    │
│  • High-Value & VIP Account Escalation       │
└──────────────────────┬───────────────────────┘
                       │ Authorized Action
                       ▼
┌──────────────────────────────────────────────┐
│       4. RECOVERY SIMULATION & AUDIT         │
│  • Synthetic Probabilistic Execution         │
│  • Immutable SQLite Audit Trail              │
│  • Analytics & 3-Way Comparative Reporting   │
└──────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **The LLM is advisory only. It cannot directly execute financial actions or modify user balances.**

---

## 🛡️ Deterministic Safety Guardrails

| Guardrail | Rule Trigger | Policy Engine Action | Audit Override Reason |
|---|---|---|---|
| **1. Idempotency Guard** | Duplicate `event_id` | `DUPLICATE_BLOCKED` | *Idempotency Guard: Event ID already processed. Duplicate blocked.* |
| **2. Action Whitelist** | Proposal $\notin$ Allowed Set | Override to `ESCALATE` | *Security Violation: Unauthorized action blocked.* |
| **3. Fraud Protection** | `SUSPECTED_FRAUD` | Strictly `NO_ACTION` | *Fraud Safety Guard: Retries/reminders forbidden to prevent chargebacks.* |
| **4. Expired Card** | `CARD_EXPIRED` | Override to `ALTERNATE_PAYMENT` | *Permanent Error Guard: Expired card retry guaranteed to fail.* |
| **5. Max Retries** | Prior Retries $\ge 3$ | Override to `ALTERNATE_PAYMENT` / `ESCALATE` | *Max Retries Exhausted: Exceeded retry limit (3/3).* |
| **6. Confidence Guard** | Confidence $< 0.65$ | Override to `ESCALATE` | *Confidence Guard: Score below safe autonomous threshold (0.65).* |
| **7. High-Value / VIP** | Amount $\ge$ ₹50,000 or VIP | Override to `ESCALATE` | *High-Value Guard: Critical transaction routed to relationship desk.* |

### Whitelisted Actions
1. `RETRY`: Automated re-attempt for transient server downtime (`BANK_SERVER_DOWN`, `NETWORK_TIMEOUT`).
2. `ALTERNATE_PAYMENT`: Prompt customer to switch instrument (`CARD_EXPIRED`, `LIMIT_EXCEEDED`).
3. `REMINDER`: 1-click notification prompt for dropouts (`AUTHENTICATION_FAILED_3DS`, `INSUFFICIENT_FUNDS`).
4. `ESCALATE`: Priority routing to human relationship managers for VIP accounts or complex declines (`DO_NOT_HONOR`).
5. `NO_ACTION`: Immediate containment and block for security flags (`SUSPECTED_FRAUD`).

---

## 📊 3-Way Strategy Comparison (100-Record Seed 42 Batch)

| Metric | RecoverAI (AI + Policy Engine) | Baseline 2 (Simple Rule-Based) | Baseline 1 (Naive Blind Retries) | Net AI Advantage vs Rule | Net AI Advantage vs Blind |
|---|---|---|---|---|---|
| **Total Revenue at Risk** | ₹3,636,475.84 | ₹3,636,475.84 | ₹3,636,475.84 | — | — |
| **Gross Recovered Revenue** | **₹2,674,177.71** | ₹2,039,557.48 | ₹1,003,861.09 | **+₹634,620.23** | **+₹1,670,316.62** |
| **Intervention Cost** | **₹2,555.00** | ₹1,155.00 | ₹5,360.00 | +₹1,400.00 | **-₹2,805.00 (Saved)** |
| **Net Recovered Revenue** | **₹2,671,622.71** | ₹2,038,402.48 | ₹998,501.09 | **+₹633,220.23 (+31.06%)** | **+₹1,673,121.62 (+167.56%)** |
| **Revenue Recovery Rate** | **73.54%** | 56.09% | 27.61% | **+17.45 percentage points** | **+45.93 percentage points** |
| **Transaction Recovery Rate** | **84.0%** (84 / 100) | 65.0% (65 / 100) | 24.0% (24 / 100) | **+19.0 percentage points** | **+60.0 percentage points** |
| **Retries Executed** | **32** (Targeted only) | 37 (Static) | 268 (Blind) | 5 retries saved | **236 retries saved** |
| **Wasted / Failed Retries** | **0** | 9 | 228 repeated failures | 9 fatigue events prevented | **228 fatigue events prevented** |
| **Policy Guardrail Overrides** | **15** safety interventions | 0 (No safety engine) | 0 (Blind) | Safe authorization enforced | Strict governance active |
| **Fraud Interventions** | **5** (100% blocked) | 5 (Blocked) | 0 (Exposed to chargebacks) | Zero fraud loss incurred | Zero fraud loss incurred |

---

## 🔬 Multi-Seed Robustness Evaluation (20 Seeds, 2,000 Transactions)

> [!NOTE]
> **What this evaluation shows, and what it doesn't:** All three strategies are scored against a hand-authored synthetic probability model ([`simulator.py`](backend/app/services/simulator.py)), not real payment gateway outcomes. Under those documented assumptions, contextual action selection outperforms static rules and blind retries **by construction** — that is the design concept the demo illustrates. What the 20-seed evaluation adds is *robustness*: it proves the strategy gap remains consistent across 20 distinct pseudo-random transaction mixes, rather than being an artifact of the seed-42 demo batch. It is **not** a claim of real-world statistical significance or live gateway production performance.

To verify that the strategy advantage is consistent across varied failure profiles, RecoverAI includes an automated 20-seed robustness evaluation across 2,000 distinct transactions:

```bash
PYTHONPATH=backend python3 backend/scripts/evaluate_seeds.py
```

### 20-Seed Aggregate Summary

| Metric | RecoverAI (AI + Policy Engine) | Simple Rule-Based Baseline | Naive Blind Retry Baseline |
|---|---|---|---|
| **Mean Gross Revenue Recovered** | **₹2,552,810.19** | ₹1,848,440.23 | ₹705,080.11 |
| **Mean Intervention Cost** | **₹2,110.50** | ₹1,201.75 | ₹5,387.00 |
| **Mean Net Revenue Recovered** | **₹2,550,699.69** (StdDev: ±₹262,215.88) | ₹1,847,238.48 | ₹699,693.11 |
| **Mean Revenue Recovery Rate** | **68.62%** | 49.91% | 18.90% |
| **Mean Transaction Recovery Rate** | **82.15%** (StdDev: ±4.22%, Median: 82.0%) | 63.05% (StdDev: ±4.37%) | 20.75% (StdDev: ±4.58%) |
| **Transaction Recovery Range** | **74.0% – 89.0%** | 57.0% – 70.0% | 11.0% – 29.0% |
| **Mean Net Revenue Uplift vs Baseline** | — | **+₹703,461.20 (+38.08%)** | **+₹1,851,006.58 (+264.55%)** |
| **Transaction Recovery Advantage** | — | **+19.10 percentage points** | **+61.40 percentage points** |

---

## 💻 Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, SQLite, Pydantic V2, Pytest, HTTPX.
- **Frontend**: React 18, Vite, Tailwind CSS, Lucide React.
- **AI Diagnostics**: Google Gemini (`gemini-1.5-flash`) / OpenAI (`gpt-4o-mini`) via environment variables with a **built-in Deterministic Heuristic Fallback Engine** (works 100% without API keys).

---

## 🚀 Local Setup & Quickstart

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run full automated test suite (15 / 15 tests pass)
PYTHONPATH=. pytest tests/test_core.py -v

# Run 20-seed robustness evaluation
PYTHONPATH=. python3 scripts/evaluate_seeds.py

# Start FastAPI backend server (http://127.0.0.1:8000)
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Build for production (verifies zero build errors)
npm run build

# Start Vite dev server (http://localhost:5173)
npm run dev
```

Open **`http://localhost:5173`** in your browser to access the dashboard.

---

## 🔑 Environment Variables & LLM Mode

RecoverAI operates **completely out-of-the-box in Deterministic Fallback Mode** without requiring any API keys.

To enable live LLM mode, copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Set your API key:
```env
GEMINI_API_KEY=<your_api_key_here>
# or
OPENAI_API_KEY=<your_api_key_here>
```
The dashboard header displays a live badge indicating whether the current run used **"LLM Mode"** or **"Deterministic Fallback Mode"**.

---

## 🎮 5-Minute Demo Walkthrough

1. **Open Dashboard**: Navigate to `http://localhost:5173`.
2. **Reset Dataset**: Click **"Reset (100)"** in the top navigation bar to generate 100 fresh synthetic failed payments.
3. **Run 3 Strategies**:
   - Click **"1. Blind Retry"** to simulate blind 3x retries.
   - Click **"2. Rule Baseline"** to simulate static rule-based recovery.
   - Click **"3. Run RecoverAI"** to execute AI diagnosis with policy engine authorization.
4. **Compare 3 Strategies**: Observe the side-by-side 3-card comparison showing RecoverAI's +₹6.33L net revenue uplift over simple rules (+31.06% net uplift, +19.0 percentage points tx recovery) and +₹16.73L net revenue uplift over blind retries.
5. **View 20-Seed Analysis**: Expand the **"Multi-Seed Robustness Evaluation"** drawer to view consistency across 2,000 simulated transactions under the documented synthetic probability model.
6. **Inspect Single Payment & Idempotency**:
   - Navigate to the **"Transactions"** tab and click **"Diagnose"** on any transaction to view the 4-stage pipeline stepper (**"AI RECOMMENDS. POLICY ENGINE DECIDES."**).
7. **Inspect Audit Trail**: Switch to the **"Audit Trail"** tab to filter by **"Overrides Only"** or **"Duplicates Blocked"**.
8. **View Safety Model**: Switch to the **"Architecture & Safety Model"** tab to inspect the zero-trust execution boundary.

---

## 🧪 Automated Test Suite

Run the full pytest suite:
```bash
PYTHONPATH=backend pytest backend/tests/test_core.py -v
```
**Tests Covered (15 / 15 Passing)**:
- `test_synthetic_payment_generation`: Synthetic dataset generation (100 records)
- `test_revenue_at_risk_calculation`: Revenue at risk & feasibility assessment
- `test_llm_diagnosis_schema_and_fallback`: LLM structured JSON output schema & fallback
- `test_policy_engine_max_retries_guard`: Policy engine max retries guard (Attempts $\ge 3$)
- `test_policy_engine_fraud_protection`: Fraud zero-tolerance guard
- `test_policy_engine_expired_card_no_retry`: Expired card auto-routing guard
- `test_policy_engine_confidence_threshold_guard`: Confidence threshold guard ($< 0.65$)
- `test_policy_engine_high_value_vip_guard`: High-value & VIP account guard
- `test_reproducibility_stable_seed_across_calls`: Reproducibility & stable seed (SHA-256)
- `test_economic_evaluation_expected_net_recovery`: Economic evaluation & expected net revenue optimization
- `test_idempotency_atomic_and_duplicate_blocked`: Atomic idempotency & duplicate event protection
- `test_baseline_independence`: Baseline independence & isolated execution
- `test_3_way_strategy_comparison_with_net_metrics`: 3-way comparative analytics with gross/cost/net metrics
- `test_multi_seed_robustness_evaluation`: Multi-seed robustness evaluation across pseudo-random datasets
- `test_api_endpoints_including_seed_reset`: FastAPI REST endpoints integration & custom seed reset

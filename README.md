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

| Metric | RecoverAI (AI + Policy) | Baseline 2 (Simple Rule-Based) | Baseline 1 (Blind Retries) | Net AI Uplift vs Rule |
|---|---|---|---|---|
| **Total Revenue at Risk** | ₹3,636,475.84 | ₹3,636,475.84 | ₹3,636,475.84 | — |
| **Simulated Revenue Recovered** | **₹2,674,741.65** | ₹1,637,123.17 | ₹402,361.01 | **+₹1,037,618.48** |
| **Simulated Transaction Recovery** | **85.0%** (85 / 100) | 60.0% (60 / 100) | 16.0% (16 / 100) | **+25.0%** |
| **Target Retries Executed** | **33** (Targeted only) | 48 (Static) | 278 (Blind) | **245 retries saved** |
| **Wasted Retries / Fatigue** | **0** | 12 | 252 repeated failures | **252 fatigue events prevented** |
| **Policy Guardrail Overrides** | **5** safety interventions | 0 (No safety engine) | 0 (Blind) | Safe authorization enforced |
| **Simulated Fraud Interventions** | **5** (100% blocked) | 5 (Blocked) | 0 (Exposed to chargebacks) | Zero fraud loss incurred |

---

## 🔬 Multi-Seed Robustness Evaluation (20 Seeds, 2,000 Transactions)

> **What this evaluation shows, and what it doesn't:** All three strategies are scored against a hand-authored synthetic probability model (`simulator.py`), not real payment gateway outcomes. Under those documented assumptions, contextual action selection outperforms static rules and blind retries **by construction** — that's the concept the demo is illustrating. What the 20-seed run actually adds is *robustness*: it shows the gap between strategies holds up consistently across 20 different random transaction mixes, rather than being a fluke of the seed-42 demo batch. It is **not** a claim of real-world statistical significance or production recovery performance.

To check that the strategy gap is not an artifact of the specific seed-42 transaction mix, RecoverAI includes a robustness evaluation across 20 distinct pseudo-random datasets:

```bash
python3 backend/scripts/evaluate_seeds.py
```

### 20-Seed Aggregate Results

| Metric | RecoverAI (AI + Policy) | Simple Rule Baseline | Blind Retry Baseline |
|---|---|---|---|
| **Mean Transaction Recovery Rate** | **85.80%** | 61.55% | 20.95% |
| **Recovery Rate Range** | **80.0% – 92.0%** | 52.0% – 68.0% | 12.0% – 30.0% |
| **Standard Deviation** | **±3.69%** | ±4.12% | ±4.68% |
| **Mean Recovered Revenue** | **₹2,694,990.34** | ₹1,841,442.19 | ₹684,717.51 |
| **Mean Net Uplift over Blind Retry** | **+64.85%** (+₹2,010,272.83) | — | — |
| **Mean Net Uplift over Rule Baseline** | **+24.25%** (+₹853,548.15) | — | — |

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
pytest tests/test_core.py -v

# Run 20-seed robustness evaluation
python3 scripts/evaluate_seeds.py

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
4. **Compare 3 Strategies**: Observe the side-by-side 3-card comparison showing RecoverAI's +₹10.38L uplift over simple rules and +₹22.72L uplift over blind retries.
5. **View 20-Seed Analysis**: Expand the **"Multi-Seed Robustness Evaluation"** drawer to view consistency across 2,000 simulated transactions under the documented synthetic probability model.
6. **Inspect Single Payment & Idempotency**:
   - Navigate to the **"Transactions"** tab and click **"Diagnose"** on any transaction to view the 4-stage pipeline stepper (**"AI RECOMMENDS. POLICY ENGINE DECIDES."**).
7. **Inspect Audit Trail**: Switch to the **"Audit Trail"** tab to filter by **"Overrides Only"** or **"Duplicates Blocked"**.
8. **View Safety Model**: Switch to the **"Architecture & Safety Model"** tab to inspect the zero-trust execution boundary.

---

## 🧪 Automated Test Suite

Run the full pytest suite:
```bash
pytest backend/tests/test_core.py -v
```
**Tests Covered (15 / 15 Passing)**:
- Synthetic dataset generation (100 records)
- Revenue at risk calculation
- LLM structured JSON output schema & fallback
- Deterministic policy engine max retries guard
- Fraud zero-tolerance guard
- Expired card guard
- Confidence threshold guard
- High-value / VIP account guard
- Authority boundary invariance
- **Idempotency: first event execution success & duplicate blocked**
- **Idempotency: distinct events execute independently**
- **Baseline 2: Rule-Based recovery simulation**
- **3-Way Strategy comparative analytics**
- **Multi-seed robustness evaluation runner**
- FastAPI REST endpoints integration

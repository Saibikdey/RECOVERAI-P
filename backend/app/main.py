from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings, get_effective_llm_mode
from app.database import engine, Base, SessionLocal
from app.models import PaymentRecord
from app.generator import generate_synthetic_payments
from app.routers import payments, recovery, audit, analytics

# Create SQLite tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Auto-seed 100 synthetic payments if database is empty
    db = SessionLocal()
    try:
        count = db.query(PaymentRecord).count()
        if count == 0:
            records = generate_synthetic_payments(count=100, seed=42)
            db.add_all(records)
            db.commit()
            print(f"[RecoverAI] Initialized database with {len(records)} synthetic failed-payment records.")
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="AI Revenue Recovery Agent with Deterministic Policy Guardrails for Razorpay AI Buildathon Track 03",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(payments.router)
app.include_router(recovery.router)
app.include_router(audit.router)
app.include_router(analytics.router)

@app.get("/api/health")
def health_check():
    effective_mode = get_effective_llm_mode()
    mode_label = "LLM Mode" if effective_mode == "llm" else "Deterministic Fallback Mode"
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "llm_mode": mode_label,
        "policy_engine": "Active (Deterministic Final Authority)",
        "allowed_actions": ["RETRY", "ALTERNATE_PAYMENT", "REMINDER", "ESCALATE", "NO_ACTION"]
    }

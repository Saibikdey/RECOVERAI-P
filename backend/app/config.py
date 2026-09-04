import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    APP_NAME: str = "RecoverAI"
    DATABASE_URL: str = "sqlite:///./recoverai.db"
    
    # LLM Configuration
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto") # "gemini", "openai", "fallback", or "auto"
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Deterministic Policy Engine Guardrails
    MAX_RETRIES: int = 3
    CONFIDENCE_THRESHOLD: float = 0.65
    COOLDOWN_HOURS: int = 4
    HIGH_VALUE_THRESHOLD_INR: float = 50000.0

settings = Settings()

def get_effective_llm_mode() -> str:
    """Returns 'llm' if an API key is configured, otherwise 'fallback'"""
    if settings.LLM_PROVIDER == "fallback":
        return "fallback"
    if settings.GEMINI_API_KEY or settings.OPENAI_API_KEY:
        return "llm"
    return "fallback"

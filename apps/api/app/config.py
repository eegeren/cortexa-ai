from __future__ import annotations
import os

class Settings:
    DATABASE_URL: str | None = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://cortexa:cortexa@db:5432/cortexa"
    )
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_EMBED_MODEL: str = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "devsecret")
    RECALL_MAX_DIST: float = float(os.getenv("RECALL_MAX_DIST", "0.8"))
    AUTO_MEMORY_MIN_SCORE: float = float(os.getenv("AUTO_MEMORY_MIN_SCORE", "0.55"))

settings = Settings()
"""Konfigurasi aplikasi dari environment variable (opsional lewat file .env)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    database_path: str = str(BASE_DIR / "chatbot.db")
    llm_provider: str = "mock"  # "gemini" | "mock"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    llm_timeout_seconds: float = 8.0
    llm_max_retries: int = 1
    admin_api_key: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(BASE_DIR / ".env")
        key = os.getenv("GEMINI_API_KEY", "").strip()
        provider = os.getenv("LLM_PROVIDER", "").strip().lower() or ("gemini" if key else "mock")
        db_path = os.getenv("DATABASE_PATH", "").strip() or "chatbot.db"
        if not os.path.isabs(db_path):
            db_path = str(BASE_DIR / db_path)
        return cls(
            database_path=db_path,
            llm_provider=provider,
            gemini_api_key=key,
            gemini_model=os.getenv("GEMINI_MODEL", cls.gemini_model).strip(),
            llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", cls.llm_timeout_seconds)),
            llm_max_retries=int(os.getenv("LLM_MAX_RETRIES", cls.llm_max_retries)),
            admin_api_key=os.getenv("ADMIN_API_KEY", "").strip(),
        )

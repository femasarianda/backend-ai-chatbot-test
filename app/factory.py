"""Application factory (memudahkan injeksi Settings/LLM saat testing)."""
from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import Settings
from app.database import init_db
from app.errors import AppError
from app.routers import billing, chat, conversations, health, knowledge
from app.services.llm import LLMClient, build_llm


def create_app(settings: Optional[Settings] = None, llm: Optional[LLMClient] = None) -> FastAPI:
    settings = settings or Settings.from_env()
    init_db(settings.database_path)  # buat tabel + seed bila belum ada (idempotent)

    app = FastAPI(
        title="Chatbot Layanan Digital",
        description="Backend chatbot berbasis FastAPI + SQLite + LLM (Gemini).",
        version="1.0.0",
    )
    app.state.settings = settings
    app.state.llm = llm or build_llm(settings)

    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}}
        )

    for module in (health, chat, billing, conversations, knowledge):
        app.include_router(module.router)
    return app

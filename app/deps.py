"""Dependency FastAPI: koneksi DB per-request, LLM, dan otorisasi admin."""
from __future__ import annotations

import hmac
import sqlite3
from typing import Iterator

from fastapi import Header, Request

from app.database import connect
from app.errors import AdminDisabled, Unauthorized
from app.services.llm import LLMClient


def get_db(request: Request) -> Iterator[sqlite3.Connection]:
    conn = connect(request.app.state.settings.database_path)
    try:
        yield conn
    finally:
        conn.close()


def get_llm(request: Request) -> LLMClient:
    return request.app.state.llm


def require_admin(request: Request, x_admin_key: str = Header(default="")) -> None:
    expected = request.app.state.settings.admin_api_key
    if not expected:
        raise AdminDisabled()
    if not hmac.compare_digest(x_admin_key.encode(), expected.encode()):
        raise Unauthorized()

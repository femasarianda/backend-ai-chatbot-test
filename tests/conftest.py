import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.factory import create_app
from app.services.llm import MockLLM

ADMIN_KEY = "test-admin-key"


@pytest.fixture
def settings(tmp_path):
    return Settings(
        database_path=str(tmp_path / "test.db"), llm_provider="mock", admin_api_key=ADMIN_KEY
    )


@pytest.fixture
def make_client(settings):
    def _make(llm=None):
        return TestClient(create_app(settings, llm or MockLLM()))

    return _make


@pytest.fixture
def client(make_client):
    return make_client()


@pytest.fixture
def db(settings, client):
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def chat(client, client_id, message, conversation_id=None):
    body = {"client_id": client_id, "message": message}
    if conversation_id:
        body["conversation_id"] = conversation_id
    return client.post("/chat", json=body)

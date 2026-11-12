import sqlite3

from fastapi import APIRouter, Depends

from app.deps import get_db, get_llm
from app.schemas import ChatRequest, ChatResponse
from app.services import chat_engine
from app.services.llm import LLMClient

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    conn: sqlite3.Connection = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
):
    """Proses pesan klien. `conversation_id` kosong -> sesi baru dibuat.

    Jika `conversation_id` sudah ada dan milik klien lain -> 403.
    """
    result = chat_engine.process_chat(conn, llm, body.client_id, body.conversation_id, body.message)
    return ChatResponse(
        conversation_id=result.conversation_id,
        client_id=result.client_id,
        reply=result.reply,
        detected_intent=result.intent,
        source=result.source,
    )

"""Orkestrasi: Intent -> Policy -> Retrieval -> Response -> Save.

Keputusan dan fakta datang dari backend (policy.decide). LLM hanya
menulis ulang gaya bahasa, dan keluarannya divalidasi sebelum dipakai.
"""
from __future__ import annotations

import re
import sqlite3
import uuid
from dataclasses import dataclass
from typing import Optional

from app import repositories as repo
from app.errors import ClientNotFound, ConversationForbidden
from app.services import policy
from app.services.intent import Intent, detect_intent
from app.services.llm import LLMClient, LLMUnavailable

_NUMBER = re.compile(r"\d+(?:[.,\-]\d+)*")


@dataclass(frozen=True)
class ChatResult:
    conversation_id: str
    client_id: str
    reply: str
    intent: str
    source: str  # "rules" | "llm"


def _numbers(text: str) -> set:
    return set(_NUMBER.findall(text))


def is_safe_rewrite(draft: str, rewritten: str) -> bool:
    """Tolak tulisan ulang LLM bila fakta numerik berubah/hilang/bertambah.

    Nominal, nomor rekening, dan angka lain harus persis sama dengan draft.
    """
    if not rewritten or len(rewritten) > 3 * len(draft) + 300:
        return False
    return _numbers(rewritten) == _numbers(draft)


def process_chat(
    conn: sqlite3.Connection,
    llm: LLMClient,
    client_id: str,
    conversation_id: Optional[str],
    message: str,
) -> ChatResult:
    client = repo.get_client(conn, client_id)
    if client is None:
        raise ClientNotFound()

    history = []
    if conversation_id:
        conv = repo.get_conversation(conn, conversation_id)
        if conv is not None:
            if conv["client_id"] != client_id:
                raise ConversationForbidden()
            history = [(r["sender"], r["message_text"]) for r in repo.recent_messages(conn, conversation_id)]
    else:
        conversation_id = f"conv-{uuid.uuid4().hex[:12]}"

    intent = detect_intent(message)
    decision = policy.decide(conn, client, message, intent)

    reply, source = decision.draft, "rules"
    if decision.allow_llm:
        try:
            candidate = llm.polish(decision.draft, message, history)
            if is_safe_rewrite(decision.draft, candidate):
                reply, source = candidate, ("llm" if llm.name != "mock" else "rules")
        except LLMUnavailable:
            pass  # fallback ke draft deterministik: chatbot tetap menjawab

    repo.append_turn(conn, conversation_id, client_id, message, reply, decision.intent.value)
    return ChatResult(conversation_id, client_id, reply, decision.intent.value, source)

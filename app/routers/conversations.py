import sqlite3

from fastapi import APIRouter, Depends, Header, Response

from app import repositories as repo
from app.deps import get_db
from app.errors import ConversationForbidden, ConversationNotFound
from app.schemas import ConversationOut, MessageOut

router = APIRouter(tags=["conversations"])


def _authorized_conversation(conn: sqlite3.Connection, conversation_id: str, client_id: str):
    conv = repo.get_conversation(conn, conversation_id)
    if conv is None:
        raise ConversationNotFound()
    if conv["client_id"] != client_id:
        raise ConversationForbidden()
    return conv


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(
    conversation_id: str,
    x_client_id: str = Header(description="ID klien pemilik sesi, mis. CLI-001"),
    conn: sqlite3.Connection = Depends(get_db),
):
    conv = _authorized_conversation(conn, conversation_id, x_client_id)
    messages = repo.list_messages(conn, conversation_id)
    return ConversationOut(
        conversation_id=conv["conversation_id"],
        client_id=conv["client_id"],
        created_at=conv["created_at"],
        updated_at=conv["updated_at"],
        messages=[
            MessageOut(**{k: m[k] for k in MessageOut.model_fields}) for m in messages
        ],
    )


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: str,
    x_client_id: str = Header(description="ID klien pemilik sesi, mis. CLI-001"),
    conn: sqlite3.Connection = Depends(get_db),
):
    _authorized_conversation(conn, conversation_id, x_client_id)
    repo.delete_conversation(conn, conversation_id)
    return Response(status_code=204)

"""Akses data (SQL). Tidak berisi aturan bisnis."""
from __future__ import annotations

import sqlite3
from typing import List, Optional

from app.database import transaction
from app.errors import ConversationForbidden


# ---- clients & invoices -------------------------------------------------
def get_client(conn: sqlite3.Connection, client_id: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM clients WHERE client_id = ?", (client_id,)).fetchone()


def list_invoices(conn: sqlite3.Connection, client_id: str) -> List[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM invoices WHERE client_id = ? ORDER BY invoice_no", (client_id,)
    ).fetchall()


def get_invoice(conn: sqlite3.Connection, invoice_no: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM invoices WHERE invoice_no = ?", (invoice_no,)).fetchone()


# ---- knowledge base -----------------------------------------------------
def list_knowledge(conn: sqlite3.Connection, category: Optional[str] = None) -> List[sqlite3.Row]:
    if category:
        return conn.execute(
            "SELECT * FROM knowledge_bases WHERE category = ? ORDER BY id", (category,)
        ).fetchall()
    return conn.execute("SELECT * FROM knowledge_bases ORDER BY id").fetchall()


def insert_knowledge(conn: sqlite3.Connection, category, triggers, title, content) -> sqlite3.Row:
    cur = conn.execute(
        "INSERT INTO knowledge_bases (category, keyword_triggers, title, content) VALUES (?,?,?,?)",
        (category, triggers, title, content),
    )
    return conn.execute("SELECT * FROM knowledge_bases WHERE id = ?", (cur.lastrowid,)).fetchone()


# ---- conversations ------------------------------------------------------
def get_conversation(conn: sqlite3.Connection, conversation_id: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM conversations WHERE conversation_id = ?", (conversation_id,)
    ).fetchone()


def list_messages(conn: sqlite3.Connection, conversation_id: str) -> List[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM chat_messages WHERE conversation_id = ? ORDER BY turn_index",
        (conversation_id,),
    ).fetchall()


def recent_messages(conn: sqlite3.Connection, conversation_id: str, limit: int = 6) -> List[sqlite3.Row]:
    rows = conn.execute(
        "SELECT sender, message_text FROM chat_messages WHERE conversation_id = ? "
        "ORDER BY turn_index DESC LIMIT ?",
        (conversation_id, limit),
    ).fetchall()
    return list(reversed(rows))


def delete_conversation(conn: sqlite3.Connection, conversation_id: str) -> None:
    conn.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))


def append_turn(
    conn: sqlite3.Connection,
    conversation_id: str,
    client_id: str,
    user_text: str,
    bot_text: str,
    intent: str,
) -> None:
    """Simpan sepasang pesan secara atomik; buat sesi baru bila belum ada.

    Kepemilikan sesi diperiksa DI DALAM transaksi sehingga dua klien yang
    memakai conversation_id yang sama secara bersamaan tidak bisa saling
    menimpa.
    """
    with transaction(conn):
        owner = conn.execute(
            "SELECT client_id FROM conversations WHERE conversation_id = ?", (conversation_id,)
        ).fetchone()
        if owner is None:
            conn.execute(
                "INSERT INTO conversations (conversation_id, client_id) VALUES (?, ?)",
                (conversation_id, client_id),
            )
        elif owner["client_id"] != client_id:
            raise ConversationForbidden()

        next_idx = conn.execute(
            "SELECT COALESCE(MAX(turn_index), 0) + 1 FROM chat_messages WHERE conversation_id = ?",
            (conversation_id,),
        ).fetchone()[0]
        conn.executemany(
            "INSERT INTO chat_messages (conversation_id, turn_index, sender, message_text, "
            "detected_intent) VALUES (?, ?, ?, ?, ?)",
            [
                (conversation_id, next_idx, "user", user_text, intent),
                (conversation_id, next_idx + 1, "assistant", bot_text, intent),
            ],
        )
        conn.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE conversation_id = ?",
            (conversation_id,),
        )


# ---- payment confirmations ---------------------------------------------
def insert_confirmation(conn: sqlite3.Connection, client_id, invoice_no, nominal, bank, sender) -> int:
    cur = conn.execute(
        "INSERT INTO payment_confirmations (client_id, invoice_no, nominal_transfer, bank_tujuan, "
        "nama_rekening_pengirim) VALUES (?,?,?,?,?)",
        (client_id, invoice_no, nominal, bank, sender),
    )
    return int(cur.lastrowid)


def get_confirmation(conn: sqlite3.Connection, confirmation_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM payment_confirmations WHERE id = ?", (confirmation_id,)
    ).fetchone()

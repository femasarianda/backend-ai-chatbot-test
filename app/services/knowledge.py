"""Knowledge retrieval: keyword matching berbobot jumlah kata trigger."""
from __future__ import annotations

import re
import sqlite3
from typing import Optional

from app import repositories as repo


def _contains(text: str, phrase: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text) is not None


def search(conn: sqlite3.Connection, message: str) -> Optional[sqlite3.Row]:
    """Kembalikan entri KB paling relevan, atau None bila tidak ada yang cocok.

    Skor = total jumlah kata dari trigger yang muncul di pesan, sehingga frasa
    ("paket seo") mengalahkan kata tunggal ("seo"). Seri dimenangkan id terkecil.
    """
    text = re.sub(r"\s+", " ", message.lower())
    best, best_score = None, 0
    for row in repo.list_knowledge(conn):
        score = 0
        for trigger in row["keyword_triggers"].split(","):
            trigger = trigger.strip().lower()
            if trigger and _contains(text, trigger):
                score += len(trigger.split())
        if score > best_score:
            best, best_score = row, score
    return best

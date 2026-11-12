"""Koneksi SQLite, inisialisasi skema, dan helper transaksi.

Satu koneksi dibuat PER REQUEST (lihat deps.get_db); tidak ada koneksi atau
state klien yang dibagi antar request.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from app.config import BASE_DIR

SCHEMA_PATH = BASE_DIR / "db" / "schema.sql"
SEED_PATH = BASE_DIR / "db" / "seed.sql"


def connect(path: str) -> sqlite3.Connection:
    # isolation_level=None -> autocommit; transaksi dikelola eksplisit.
    conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def init_db(path: str, seed: bool = True) -> None:
    conn = connect(path)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        if seed:
            conn.executescript(SEED_PATH.read_text(encoding="utf-8"))
    finally:
        conn.close()


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[None]:
    """BEGIN IMMEDIATE agar penulisan antar-request diserialisasi."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")

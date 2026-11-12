"""Membuat tabel dan mengisi data simulasi.

Pemakaian:
    python init_db.py            # buat tabel + seed (idempotent)
    python init_db.py --reset    # hapus file DB lalu buat ulang
"""
import argparse
import os

from app.config import Settings
from app.database import init_db


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="hapus DB lama dulu")
    args = parser.parse_args()

    path = Settings.from_env().database_path
    if args.reset and os.path.exists(path):
        os.remove(path)
        for suffix in ("-wal", "-shm"):
            if os.path.exists(path + suffix):
                os.remove(path + suffix)
    init_db(path)
    print(f"Database siap: {path}")


if __name__ == "__main__":
    main()

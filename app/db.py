import sqlite3
from pathlib import Path

DB_PATH = Path("data/leads.db")


def get_conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                name TEXT,
                email TEXT,
                phone TEXT,
                message TEXT,
                score TEXT,
                category TEXT,
                summary TEXT,
                suggested_reply TEXT,
                status TEXT DEFAULT 'new'
            )
        """)

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "leads.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                interested_course TEXT NOT NULL,
                enquiry_message TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Check whether the follow-up column already exists.
        columns = [
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(leads)"
            ).fetchall()
        ]

        # Add the column only if it does not exist.
        if "follow_up_at" not in columns:
            connection.execute(
                "ALTER TABLE leads ADD COLUMN follow_up_at TEXT"
            )

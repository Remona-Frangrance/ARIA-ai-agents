import sqlite3
import os
from datetime import date, datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "wellness.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS wellness_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT CHECK(type IN ('sleep', 'hydration', 'mood', 'activity')) NOT NULL,
            value REAL NOT NULL,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );
    """)
    conn.commit()
    conn.close()

def log_wellness(log_type, value, notes=None, log_date=None):
    conn = get_connection()
    if not log_date:
        log_date = date.today().isoformat()
    conn.execute(
        "INSERT INTO wellness_logs (date, type, value, notes) VALUES (?, ?, ?, ?)",
        (log_date, log_type, value, notes)
    )
    conn.commit()
    conn.close()

def get_wellness_summary():
    conn = get_connection()
    # Get last 7 days for charts
    logs = conn.execute("SELECT * FROM wellness_logs ORDER BY date DESC LIMIT 50").fetchall()
    conn.close()
    return [dict(l) for l in logs]

init_db()

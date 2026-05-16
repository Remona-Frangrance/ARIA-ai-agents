import sqlite3
import os
from datetime import date, datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "relationships.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            tier TEXT CHECK(tier IN ('inner', 'close', 'network')) DEFAULT 'close',
            birthday TEXT,
            interests TEXT,
            notes TEXT,
            avatar TEXT
        );

        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER,
            date TEXT NOT NULL,
            type TEXT DEFAULT 'message',
            sentiment REAL DEFAULT 0.5,
            summary TEXT,
            FOREIGN KEY(contact_id) REFERENCES contacts(id)
        );
    """)
    
    conn.commit()
    conn.close()

def get_contacts():
    conn = get_connection()
    contacts = conn.execute("SELECT * FROM contacts").fetchall()
    result = []
    for c in contacts:
        contact_dict = dict(c)
        last_interaction = conn.execute(
            "SELECT date, sentiment FROM interactions WHERE contact_id = ? ORDER BY date DESC LIMIT 1",
            (c['id'],)
        ).fetchone()
        contact_dict['last_contact'] = last_interaction['date'] if last_interaction else "Never"
        contact_dict['health'] = int((last_interaction['sentiment'] * 100)) if last_interaction else 50
        result.append(contact_dict)
    conn.close()
    return result

def add_interaction(contact_id, sentiment, summary):
    conn = get_connection()
    conn.execute(
        "INSERT INTO interactions (contact_id, date, sentiment, summary) VALUES (?, ?, ?, ?)",
        (contact_id, date.today().isoformat(), sentiment, summary)
    )
    conn.commit()
    conn.close()

init_db()

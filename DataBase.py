import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

# Database path from environment or default
DB_PATH = os.environ.get("DB_PATH", "faq_data.db")

def get_connection():
    """Return a new DB connection."""
    return sqlite3.connect(DB_PATH)

def create_table():
    """Create FAQ table if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faq (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            keywords TEXT,
            reference TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_faq(question, answer, keywords, reference=None):
    """Insert a new FAQ entry into DB."""
    conn = get_connection()
    cursor = conn.cursor()
    keywords_str = ', '.join(keywords) if keywords else ''
    cursor.execute('''
        INSERT INTO faq (question, answer, keywords, reference)
        VALUES (?, ?, ?, ?)
    ''', (question, answer, keywords_str, reference))
    conn.commit()
    conn.close()

def get_all_faqs():
    """Return all FAQs as a list of dicts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, question, answer, keywords, reference FROM faq")
    rows = cursor.fetchall()
    conn.close()

    faqs = []
    for row in rows:
        faqs.append({
            "question_id": row[0],
            "question": row[1],
            "answer": row[2],
            "keywords": [kw.strip() for kw in row[3].split(',')] if row[3] else [],
            "reference": row[4] if row[4] else ""
        })
    return faqs

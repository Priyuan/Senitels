import sqlite3
import os
from typing import List, Tuple, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "claims.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verified_claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim TEXT UNIQUE,
            verdict TEXT,
            confidence REAL,
            evidence_summary TEXT,
            sources TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def claim_exists(claim: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM verified_claims WHERE claim = ?", (claim,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def get_existing_claim(claim: str) -> Optional[Tuple]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM verified_claims WHERE claim = ?", (claim,))
    row = cursor.fetchone()
    conn.close()
    return row

def insert_claim(claim: str, verdict: str, confidence: float,
                 evidence_summary: str, sources: List[str]) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO verified_claims (claim, verdict, confidence, evidence_summary, sources)
            VALUES (?, ?, ?, ?, ?)
        """, (claim, verdict, confidence, evidence_summary, ",".join(sources)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_all_claims() -> List[Tuple]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT claim, verdict, timestamp FROM verified_claims ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows
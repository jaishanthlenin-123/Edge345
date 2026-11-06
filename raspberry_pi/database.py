"""
SQLite Telemetry & Anomaly Event Database Layer
Project: SG90 Servo Motor Condition Monitoring and Anomaly Detection System
Target: Raspberry Pi 5
"""

import sqlite3
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from raspberry_pi.config import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection configured for thread safety and row dicts."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes tables for sessions, telemetry records, and alert events."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Recording sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        session_name TEXT NOT NULL,
        mode TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT,
        record_count INTEGER DEFAULT 0,
        notes TEXT
    );
    """)

    # 2. High-resolution telemetry history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        host_timestamp TEXT NOT NULL,
        timestamp_ms INTEGER NOT NULL,
        sequence INTEGER NOT NULL,
        servo_angle INTEGER NOT NULL,
        voltage_v REAL NOT NULL,
        current_a REAL NOT NULL,
        accel_x INTEGER NOT NULL,
        accel_y INTEGER NOT NULL,
        accel_z INTEGER NOT NULL,
        sound_rms REAL NOT NULL,
        sound_p2p INTEGER NOT NULL,
        anomaly_score REAL DEFAULT 0.0,
        is_anomaly INTEGER DEFAULT 0,
        FOREIGN KEY(session_id) REFERENCES sessions(session_id)
    );
    """)

    # 3. Anomaly alerts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        session_id TEXT,
        severity TEXT NOT NULL,
        channel TEXT NOT NULL,
        message TEXT NOT NULL,
        reading_value REAL,
        threshold_value REAL,
        acknowledged INTEGER DEFAULT 0
    );
    """)

    # Indices for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_session ON telemetry(session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_time ON telemetry(host_timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_time ON alerts(timestamp);")

    conn.commit()
    conn.close()


def create_session(session_name: str, mode: str = "normal", notes: str = "") -> str:
    """Creates a new recording session and returns its unique ID."""
    init_db()
    conn = get_connection()
    session_id = f"{mode}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    start_time = datetime.datetime.now().isoformat()

    conn.execute(
        "INSERT INTO sessions (session_id, session_name, mode, start_time, notes) VALUES (?, ?, ?, ?, ?)",
        (session_id, session_name, mode, start_time, notes)
    )
    conn.commit()
    conn.close()
    return session_id


def close_session(session_id: str, count: int):
    """Closes a session with final record count and end time."""
    conn = get_connection()
    end_time = datetime.datetime.now().isoformat()
    conn.execute(
        "UPDATE sessions SET end_time = ?, record_count = ? WHERE session_id = ?",
        (end_time, count, session_id)
    )
    conn.commit()
    conn.close()


def insert_telemetry_batch(records: List[Dict[str, Any]], session_id: Optional[str] = None):
    """Batch-inserts telemetry rows for high throughput."""
    if not records:
        return
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO telemetry (
        session_id, host_timestamp, timestamp_ms, sequence, servo_angle,
        voltage_v, current_a, accel_x, accel_y, accel_z, sound_rms, sound_p2p,
        anomaly_score, is_anomaly
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    rows = []
    for r in records:
        rows.append((
            session_id,
            r["host_timestamp"],
            r["timestamp_ms"],
            r["sequence"],
            r["servo_angle"],
            r["voltage_v"],
            r["current_a"],
            r["accel_x"],
            r["accel_y"],
            r["accel_z"],
            r["sound_rms"],
            r["sound_p2p"],
            r.get("anomaly_score", 0.0),
            1 if r.get("is_anomaly") else 0
        ))
    cursor.executemany(query, rows)
    conn.commit()
    conn.close()


def insert_alert(severity: str, channel: str, message: str, reading: float, threshold: float, session_id: Optional[str] = None):
    """Logs an anomaly alert to the database."""
    conn = get_connection()
    ts = datetime.datetime.now().isoformat()
    conn.execute(
        "INSERT INTO alerts (timestamp, session_id, severity, channel, message, reading_value, threshold_value) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (ts, session_id, severity, channel, message, reading, threshold)
    )
    conn.commit()
    conn.close()


def get_recent_telemetry(limit: int = 100) -> List[Dict[str, Any]]:
    """Fetches the latest telemetry points for real-time charting."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM telemetry ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]


def get_recent_alerts(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetches recent anomaly alert logs."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

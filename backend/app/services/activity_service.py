import sqlite3
from pathlib import Path
from datetime import datetime, timezone


# Store the database inside the backend directory
BACKEND_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BACKEND_DIR / "network_activity.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


# Initialize the activity database
def initialize_database():

    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                source TEXT,
                destination TEXT,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                description TEXT
            )
        """)

        connection.commit()


# Record a network activity
def log_activity(
    event_type,
    action,
    source=None,
    destination=None,
    status="SUCCESS",
    description=None
):

    timestamp = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:

        connection.execute("""
            INSERT INTO activity_logs (
                timestamp,
                event_type,
                source,
                destination,
                action,
                status,
                description
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            event_type,
            source,
            destination,
            action,
            status,
            description
        ))

        connection.commit()


# Retrieve recent activities
def get_recent_activities(limit=20):

    with get_connection() as connection:

        rows = connection.execute("""
            SELECT *
            FROM activity_logs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [dict(row) for row in rows]


# Initialize database when the service is imported
initialize_database()

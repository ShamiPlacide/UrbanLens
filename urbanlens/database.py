import sqlite3
from datetime import datetime

import bcrypt
from flask import current_app


def _add_column(conn, table, column, col_type):
    """Add a column to an existing table if it doesn't already exist."""
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    except sqlite3.OperationalError:
        pass  # Column already exists


def get_db():
    conn = sqlite3.connect(current_app.config["DB_PATH"])
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            email      TEXT    NOT NULL UNIQUE,
            password   TEXT    NOT NULL,
            role       TEXT    NOT NULL CHECK(role IN ('Planner','Authority','Researcher')),
            created_at TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS settlements (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            name                TEXT NOT NULL,
            polygon_coordinates TEXT NOT NULL,
            population_estimate INTEGER,
            risk_level          TEXT DEFAULT 'Low',
            housing_type        TEXT,
            notes               TEXT,
            area                REAL,
            density             REAL,
            status              TEXT NOT NULL DEFAULT 'Pending'
                                    CHECK(status IN ('Pending','Approved','Rejected')),
            created_by          INTEGER REFERENCES users(id),
            created_at          TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at          TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS infrastructure (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            settlement_id   INTEGER REFERENCES settlements(id) ON DELETE CASCADE,
            type            TEXT NOT NULL CHECK(type IN (
                'Road','Water Point','Sanitation','Waste Point','School','Health Center'
            )),
            name            TEXT NOT NULL,
            geometry_type   TEXT NOT NULL CHECK(geometry_type IN ('Point','LineString','Polygon')),
            coordinates     TEXT NOT NULL,
            condition       TEXT CHECK(condition IN ('Good','Fair','Poor','Critical')),
            notes           TEXT,
            created_by      INTEGER REFERENCES users(id),
            created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at      TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER REFERENCES users(id),
            action      TEXT NOT NULL,
            target_type TEXT,
            target_id   INTEGER,
            detail      TEXT,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migrations: add any missing columns to existing tables
    _add_column(conn, "settlements", "housing_type", "TEXT")
    _add_column(conn, "settlements", "notes", "TEXT")
    _add_column(conn, "settlements", "status", "TEXT DEFAULT 'Approved'")
    _add_column(conn, "settlements", "created_by", "INTEGER")
    _add_column(conn, "settlements", "updated_at", "TEXT")
    _add_column(conn, "settlements", "area", "REAL")
    _add_column(conn, "settlements", "density", "REAL")

    conn.commit()

    existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing == 0:
        _create_user(conn, "Admin Planner", "admin@urbanlens.com", "admin123", "Planner")
        _create_user(conn, "Municipal Authority", "authority@urbanlens.com", "auth123", "Authority")
        _create_user(conn, "Researcher", "researcher@urbanlens.com", "research123", "Researcher")
        conn.commit()
        print("  Seeded 3 default users.")

    conn.close()


def _create_user(conn, name, email, password, role):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn.execute(
        "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
        (name, email, hashed, role),
    )


def log_action(user_id, action, target_type=None, target_id=None, detail=None):
    conn = get_db()
    conn.execute(
        "INSERT INTO audit_log (user_id, action, target_type, target_id, detail, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, action, target_type, target_id, detail, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()

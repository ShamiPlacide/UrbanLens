from datetime import datetime

import bcrypt
import psycopg2
import psycopg2.extras
from flask import current_app


def get_db():
    conn = psycopg2.connect(current_app.config["DATABASE_URL"])
    conn.autocommit = False
    return conn


def _execute(conn, query, params=None):
    """Execute a query and return the cursor. Uses RealDictCursor for dict-like rows."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(query, params)
    return cur


def _fetchone(conn, query, params=None):
    cur = _execute(conn, query, params)
    return cur.fetchone()


def _fetchall(conn, query, params=None):
    cur = _execute(conn, query, params)
    return cur.fetchall()


def _add_column(conn, table, column, col_type):
    """Add a column to an existing table if it doesn't already exist."""
    try:
        cur = conn.cursor()
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        conn.commit()
    except psycopg2.errors.DuplicateColumn:
        conn.rollback()


def init_db(database_url):
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         SERIAL PRIMARY KEY,
            name       TEXT    NOT NULL,
            email      TEXT    NOT NULL UNIQUE,
            password   TEXT    NOT NULL,
            role       TEXT    NOT NULL CHECK(role IN ('Planner','Authority','Researcher')),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settlements (
            id                  SERIAL PRIMARY KEY,
            name                TEXT NOT NULL,
            polygon_coordinates TEXT NOT NULL,
            population_estimate INTEGER,
            risk_level          TEXT DEFAULT 'Low',
            housing_type        TEXT,
            notes               TEXT,
            area                DOUBLE PRECISION,
            density             DOUBLE PRECISION,
            status              TEXT NOT NULL DEFAULT 'Pending'
                                    CHECK(status IN ('Pending','Approved','Rejected')),
            created_by          INTEGER REFERENCES users(id),
            created_at          TIMESTAMP DEFAULT NOW(),
            updated_at          TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS infrastructure (
            id              SERIAL PRIMARY KEY,
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
            created_at      TIMESTAMP DEFAULT NOW(),
            updated_at      TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER REFERENCES users(id),
            action      TEXT NOT NULL,
            target_type TEXT,
            target_id   INTEGER,
            detail      TEXT,
            created_at  TIMESTAMP DEFAULT NOW()
        )
    """)

    # Migrations: add any missing columns to existing tables
    _add_column(conn, "settlements", "housing_type", "TEXT")
    _add_column(conn, "settlements", "notes", "TEXT")
    _add_column(conn, "settlements", "status", "TEXT DEFAULT 'Approved'")
    _add_column(conn, "settlements", "created_by", "INTEGER")
    _add_column(conn, "settlements", "updated_at", "TIMESTAMP")
    _add_column(conn, "settlements", "area", "DOUBLE PRECISION")
    _add_column(conn, "settlements", "density", "DOUBLE PRECISION")

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM users")
    existing = cur.fetchone()[0]
    if existing == 0:
        _create_user(conn, "Admin Planner", "admin@urbanlens.com", "admin123", "Planner")
        _create_user(conn, "Municipal Authority", "authority@urbanlens.com", "auth123", "Authority")
        _create_user(conn, "Researcher", "researcher@urbanlens.com", "research123", "Researcher")
        conn.commit()
        print("  Seeded 3 default users.")

    conn.close()


def _create_user(conn, name, email, password, role):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
        (name, email, hashed, role),
    )


def log_action(user_id, action, target_type=None, target_id=None, detail=None):
    conn = get_db()
    _execute(
        conn,
        "INSERT INTO audit_log (user_id, action, target_type, target_id, detail, created_at) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (user_id, action, target_type, target_id, detail, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()

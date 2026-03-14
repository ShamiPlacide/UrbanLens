import sqlite3
import json
import os
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, render_template, session
import bcrypt

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "urbanlens_dev_secret_2024")
DB_PATH = "urbanlens.db"

# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

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
            status              TEXT NOT NULL DEFAULT 'Pending'
                                    CHECK(status IN ('Pending','Approved','Rejected')),
            created_by          INTEGER REFERENCES users(id),
            created_at          TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at          TEXT DEFAULT CURRENT_TIMESTAMP
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

    conn.commit()

    existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing == 0:
        _create_user(conn, "Admin Planner",      "admin@urbanlens.com",      "admin123",   "Planner")
        _create_user(conn, "Municipal Authority", "authority@urbanlens.com",  "auth123",    "Authority")
        _create_user(conn, "Researcher",          "researcher@urbanlens.com", "research123","Researcher")
        conn.commit()
        print("  Seeded 3 default users.")

    conn.close()


def _create_user(conn, name, email, password, role):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn.execute(
        "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
        (name, email, hashed, role)
    )


def log_action(user_id, action, target_type=None, target_id=None, detail=None):
    conn = get_db()
    conn.execute(
        "INSERT INTO audit_log (user_id, action, target_type, target_id, detail, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, action, target_type, target_id, detail, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# ROLE GUARDS
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return jsonify({"error": "Unauthorized"}), 401
            if session.get("role") not in roles:
                return jsonify({"error": "Forbidden — insufficient role"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


# ─────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────

@app.route("/login", methods=["POST"])
def login():
    data     = request.get_json()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not user or not bcrypt.checkpw(password.encode(), user["password"].encode()):
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

    session["user_id"] = user["id"]
    session["email"]   = user["email"]
    session["name"]    = user["name"]
    session["role"]    = user["role"]
    log_action(user["id"], "login")

    return jsonify({"success": True, "user": {
        "id": user["id"], "name": user["name"],
        "email": user["email"], "role": user["role"]
    }})


@app.route("/logout", methods=["POST"])
def logout():
    if "user_id" in session:
        log_action(session["user_id"], "logout")
    session.clear()
    return jsonify({"success": True})


@app.route("/me", methods=["GET"])
@login_required
def me():
    return jsonify({
        "id": session["user_id"], "name": session["name"],
        "email": session["email"], "role": session["role"]
    })


# ─────────────────────────────────────────────
# USER MANAGEMENT  (Authority only)
# ─────────────────────────────────────────────

@app.route("/users", methods=["GET"])
@roles_required("Authority")
def get_users():
    conn = get_db()
    rows = conn.execute("SELECT id, name, email, role, created_at FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/users", methods=["POST"])
@roles_required("Authority")
def create_user():
    data     = request.get_json()
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    role     = data.get("role", "").strip()

    if not all([name, email, password, role]):
        return jsonify({"error": "All fields are required"}), 400
    if role not in ("Planner", "Authority", "Researcher"):
        return jsonify({"error": "Invalid role"}), 400

    conn = get_db()
    if conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
        conn.close()
        return jsonify({"error": "Email already registered"}), 409

    try:
        _create_user(conn, name, email, password, role)
        conn.commit()
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        log_action(session["user_id"], "create_user", "user", new_id, f"{email} ({role})")
        return jsonify({"success": True, "id": new_id}), 201
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


@app.route("/users/<int:user_id>", methods=["DELETE"])
@roles_required("Authority")
def delete_user(user_id):
    if user_id == session["user_id"]:
        return jsonify({"error": "Cannot delete your own account"}), 400
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    log_action(session["user_id"], "delete_user", "user", user_id)
    return jsonify({"success": True})


@app.route("/users/<int:user_id>/password", methods=["PUT"])
@login_required
def change_password(user_id):
    if session["user_id"] != user_id and session["role"] != "Authority":
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json()
    new_password = data.get("new_password", "").strip()
    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    conn = get_db()
    conn.execute("UPDATE users SET password = ? WHERE id = ?", (hashed, user_id))
    conn.commit()
    conn.close()
    log_action(session["user_id"], "change_password", "user", user_id)
    return jsonify({"success": True})


# ─────────────────────────────────────────────
# SETTLEMENTS
# ─────────────────────────────────────────────

def row_to_settlement(row):
    return {
        "id":                  row["id"],
        "name":                row["name"],
        "polygon_coordinates": json.loads(row["polygon_coordinates"]),
        "population_estimate": row["population_estimate"],
        "risk_level":          row["risk_level"],
        "housing_type":        row["housing_type"],
        "notes":               row["notes"],
        "status":              row["status"],
        "created_by":          row["created_by"],
        "created_at":          row["created_at"],
        "updated_at":          row["updated_at"]
    }


@app.route("/settlements", methods=["GET"])
@login_required
def get_settlements():
    conn = get_db()
    if session["role"] == "Researcher":
        rows = conn.execute(
            "SELECT * FROM settlements WHERE status = 'Approved' ORDER BY created_at DESC"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM settlements ORDER BY created_at DESC"
        ).fetchall()
    conn.close()
    return jsonify([row_to_settlement(r) for r in rows])


@app.route("/settlements", methods=["POST"])
@roles_required("Planner", "Authority")
def create_settlement():
    data = request.get_json()
    name                = data.get("name", "").strip()
    polygon_coordinates = data.get("polygon_coordinates")
    population_estimate = data.get("population_estimate")
    risk_level          = data.get("risk_level", "Low")
    housing_type        = data.get("housing_type", "")
    notes               = data.get("notes", "")

    if not name or not polygon_coordinates:
        return jsonify({"error": "Name and coordinates are required"}), 400

    now = datetime.utcnow().isoformat()
    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO settlements
           (name, polygon_coordinates, population_estimate, risk_level,
            housing_type, notes, status, created_by, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?, ?, ?)""",
        (name, json.dumps(polygon_coordinates), population_estimate,
         risk_level, housing_type, notes, session["user_id"], now, now)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    log_action(session["user_id"], "create_settlement", "settlement", new_id, name)
    return jsonify({"success": True, "id": new_id}), 201


@app.route("/settlements/<int:settlement_id>", methods=["PUT"])
@roles_required("Planner", "Authority")
def update_settlement(settlement_id):
    data = request.get_json()
    conn = get_db()
    row  = conn.execute("SELECT * FROM settlements WHERE id = ?", (settlement_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    name                = data.get("name",                row["name"])
    polygon_coordinates = data.get("polygon_coordinates", json.loads(row["polygon_coordinates"]))
    population_estimate = data.get("population_estimate", row["population_estimate"])
    risk_level          = data.get("risk_level",          row["risk_level"])
    housing_type        = data.get("housing_type",        row["housing_type"])
    notes               = data.get("notes",               row["notes"])
    now                 = datetime.utcnow().isoformat()

    conn.execute(
        """UPDATE settlements SET
            name=?, polygon_coordinates=?, population_estimate=?,
            risk_level=?, housing_type=?, notes=?, updated_at=?
           WHERE id=?""",
        (name, json.dumps(polygon_coordinates), population_estimate,
         risk_level, housing_type, notes, now, settlement_id)
    )
    conn.commit()
    conn.close()
    log_action(session["user_id"], "update_settlement", "settlement", settlement_id, name)
    return jsonify({"success": True})


@app.route("/settlements/<int:settlement_id>/status", methods=["PUT"])
@roles_required("Authority")
def update_settlement_status(settlement_id):
    data   = request.get_json()
    status = data.get("status", "").strip()
    if status not in ("Approved", "Rejected", "Pending"):
        return jsonify({"error": "Invalid status"}), 400
    conn = get_db()
    conn.execute("UPDATE settlements SET status=?, updated_at=? WHERE id=?",
                 (status, datetime.utcnow().isoformat(), settlement_id))
    conn.commit()
    conn.close()
    log_action(session["user_id"], f"settlement_{status.lower()}", "settlement", settlement_id)
    return jsonify({"success": True})


@app.route("/settlements/<int:settlement_id>", methods=["DELETE"])
@roles_required("Planner", "Authority")
def delete_settlement(settlement_id):
    conn = get_db()
    row  = conn.execute("SELECT name FROM settlements WHERE id=?", (settlement_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404
    conn.execute("DELETE FROM settlements WHERE id = ?", (settlement_id,))
    conn.commit()
    conn.close()
    log_action(session["user_id"], "delete_settlement", "settlement", settlement_id, row["name"])
    return jsonify({"success": True})


# ─────────────────────────────────────────────
# AUDIT LOG  (Authority only)
# ─────────────────────────────────────────────

@app.route("/audit-log", methods=["GET"])
@roles_required("Authority")
def get_audit_log():
    conn = get_db()
    rows = conn.execute("""
        SELECT a.id, a.action, a.target_type, a.target_id, a.detail, a.created_at,
               u.name as user_name, u.email as user_email, u.role as user_role
        FROM audit_log a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.created_at DESC LIMIT 200
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("\n🗺  UrbanLens v2 running at http://localhost:5000")
    print("   Planner:    admin@urbanlens.com / admin123")
    print("   Authority:  authority@urbanlens.com / auth123")
    print("   Researcher: researcher@urbanlens.com / research123\n")
    app.run(debug=True, port=5000)

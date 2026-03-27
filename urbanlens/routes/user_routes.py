import bcrypt
from flask import Blueprint, request, jsonify, session

from urbanlens.auth import login_required, roles_required
from urbanlens.database import get_db, _create_user, log_action

user_bp = Blueprint("users", __name__)


@user_bp.route("/users", methods=["GET"])
@roles_required("Planner")
def get_users():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name, email, role, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@user_bp.route("/users", methods=["POST"])
@roles_required("Planner")
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    role = data.get("role", "").strip()

    if not all([name, email, password, role]):
        return jsonify({"error": "All fields are required"}), 400
    if role not in ("Planner", "Authority", "Researcher"):
        return jsonify({"error": "Invalid role"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

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


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
@roles_required("Planner")
def delete_user(user_id):
    if user_id == session["user_id"]:
        return jsonify({"error": "Cannot delete your own account"}), 400
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    log_action(session["user_id"], "delete_user", "user", user_id)
    return jsonify({"success": True})


@user_bp.route("/users/<int:user_id>/password", methods=["PUT"])
@login_required
def change_password(user_id):
    if session["user_id"] != user_id and session["role"] != "Planner":
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400
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

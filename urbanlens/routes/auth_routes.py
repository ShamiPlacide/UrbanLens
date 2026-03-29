import bcrypt
from flask import Blueprint, request, jsonify, session, render_template

from urbanlens.auth import login_required
from urbanlens.database import get_db, _fetchone, _execute, log_action

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    return render_template("index.html")


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    conn = get_db()
    user = _fetchone(conn, "SELECT * FROM users WHERE email = %s", (email,))
    conn.close()

    if not user or not bcrypt.checkpw(password.encode(), user["password"].encode()):
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

    session["user_id"] = user["id"]
    session["email"] = user["email"]
    session["name"] = user["name"]
    session["role"] = user["role"]
    log_action(user["id"], "login")

    return jsonify({
        "success": True,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
        },
    })


@auth_bp.route("/logout", methods=["POST"])
def logout():
    if "user_id" in session:
        log_action(session["user_id"], "logout")
    session.clear()
    return jsonify({"success": True})


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    return jsonify({
        "id": session["user_id"],
        "name": session["name"],
        "email": session["email"],
        "role": session["role"],
    })


@auth_bp.route("/profile", methods=["PUT"])
@login_required
def update_profile():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400

    conn = get_db()
    _execute(conn, "UPDATE users SET name = %s WHERE id = %s", (name, session["user_id"]))
    conn.commit()
    conn.close()

    session["name"] = name
    log_action(session["user_id"], "update_profile", "user", session["user_id"], name)
    return jsonify({"success": True})

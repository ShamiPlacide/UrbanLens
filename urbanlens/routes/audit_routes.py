from flask import Blueprint, jsonify

from urbanlens.auth import roles_required
from urbanlens.database import get_db, _fetchall

audit_bp = Blueprint("audit", __name__)


@audit_bp.route("/audit-log", methods=["GET"])
@roles_required("Planner")
def get_audit_log():
    conn = get_db()
    rows = _fetchall(conn, """
        SELECT a.id, a.action, a.target_type, a.target_id, a.detail, a.created_at,
               u.name as user_name, u.email as user_email, u.role as user_role
        FROM audit_log a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.created_at DESC LIMIT 200
    """)
    conn.close()
    return jsonify([dict(r) for r in rows])

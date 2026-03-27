import json
from datetime import datetime

from flask import Blueprint, request, jsonify, session

from urbanlens.auth import login_required, roles_required
from urbanlens.database import get_db, log_action
from urbanlens.models import row_to_infrastructure

infrastructure_bp = Blueprint("infrastructure", __name__)


@infrastructure_bp.route("/infrastructure", methods=["GET"])
@login_required
def get_infrastructure():
    conn = get_db()
    settlement_id = request.args.get("settlement_id", type=int)
    infra_type = request.args.get("type", "").strip()

    conditions = []
    params = []

    if settlement_id:
        conditions.append("settlement_id = ?")
        params.append(settlement_id)
    if infra_type:
        conditions.append("type = ?")
        params.append(infra_type)

    where = " AND ".join(conditions) if conditions else "1=1"
    rows = conn.execute(
        f"SELECT * FROM infrastructure WHERE {where} ORDER BY created_at DESC",
        params,
    ).fetchall()
    conn.close()
    return jsonify([row_to_infrastructure(r) for r in rows])


@infrastructure_bp.route("/infrastructure", methods=["POST"])
@roles_required("Planner", "Authority")
def create_infrastructure():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    settlement_id = data.get("settlement_id")
    infra_type = data.get("type", "").strip()
    name = data.get("name", "").strip()
    geometry_type = data.get("geometry_type", "").strip()
    coordinates = data.get("coordinates")
    condition = data.get("condition", "").strip() or None
    notes = data.get("notes", "").strip()

    if not all([settlement_id, infra_type, name, geometry_type, coordinates]):
        return jsonify({"error": "settlement_id, type, name, geometry_type, and coordinates are required"}), 400

    valid_types = ("Road", "Water Point", "Sanitation", "Waste Point", "School", "Health Center")
    if infra_type not in valid_types:
        return jsonify({"error": f"Invalid type. Must be one of: {', '.join(valid_types)}"}), 400
    if geometry_type not in ("Point", "LineString", "Polygon"):
        return jsonify({"error": "geometry_type must be Point, LineString, or Polygon"}), 400
    if condition and condition not in ("Good", "Fair", "Poor", "Critical"):
        return jsonify({"error": "condition must be Good, Fair, Poor, or Critical"}), 400

    now = datetime.utcnow().isoformat()
    conn = get_db()

    # Verify settlement exists
    if not conn.execute("SELECT id FROM settlements WHERE id = ?", (settlement_id,)).fetchone():
        conn.close()
        return jsonify({"error": "Settlement not found"}), 404

    cursor = conn.execute(
        """INSERT INTO infrastructure
           (settlement_id, type, name, geometry_type, coordinates, condition, notes,
            created_by, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            settlement_id, infra_type, name, geometry_type,
            json.dumps(coordinates), condition, notes,
            session["user_id"], now, now,
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    log_action(session["user_id"], "create_infrastructure", "infrastructure", new_id, f"{infra_type}: {name}")
    return jsonify({"success": True, "id": new_id}), 201


@infrastructure_bp.route("/infrastructure/<int:infra_id>", methods=["PUT"])
@roles_required("Planner", "Authority")
def update_infrastructure(infra_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    conn = get_db()
    row = conn.execute("SELECT * FROM infrastructure WHERE id = ?", (infra_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    if session["role"] == "Authority" and row["created_by"] != session["user_id"]:
        conn.close()
        return jsonify({"error": "You can only edit your own infrastructure"}), 403

    try:
        existing_coords = json.loads(row["coordinates"])
    except (json.JSONDecodeError, TypeError):
        existing_coords = []

    name = data.get("name", row["name"])
    infra_type = data.get("type", row["type"])
    geometry_type = data.get("geometry_type", row["geometry_type"])
    coordinates = data.get("coordinates", existing_coords)
    condition = data.get("condition", row["condition"])
    notes = data.get("notes", row["notes"])

    now = datetime.utcnow().isoformat()
    conn.execute(
        """UPDATE infrastructure SET
            type=?, name=?, geometry_type=?, coordinates=?,
            condition=?, notes=?, updated_at=?
           WHERE id=?""",
        (infra_type, name, geometry_type, json.dumps(coordinates), condition, notes, now, infra_id),
    )
    conn.commit()
    conn.close()
    log_action(session["user_id"], "update_infrastructure", "infrastructure", infra_id, f"{infra_type}: {name}")
    return jsonify({"success": True})


@infrastructure_bp.route("/infrastructure/<int:infra_id>", methods=["DELETE"])
@roles_required("Planner", "Authority")
def delete_infrastructure(infra_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM infrastructure WHERE id = ?", (infra_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    if session["role"] == "Authority" and row["created_by"] != session["user_id"]:
        conn.close()
        return jsonify({"error": "You can only delete your own infrastructure"}), 403

    conn.execute("DELETE FROM infrastructure WHERE id = ?", (infra_id,))
    conn.commit()
    conn.close()
    log_action(session["user_id"], "delete_infrastructure", "infrastructure", infra_id, row["name"])
    return jsonify({"success": True})

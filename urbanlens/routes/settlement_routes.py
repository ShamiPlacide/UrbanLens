import json
import math
from datetime import datetime

from flask import Blueprint, request, jsonify, session

from urbanlens.auth import login_required, roles_required
from urbanlens.database import get_db, _execute, _fetchone, _fetchall, log_action
from urbanlens.models import row_to_settlement

settlement_bp = Blueprint("settlements", __name__)


def compute_polygon_area(coords):
    """Compute area in sq km using the Shoelace formula on lat/lng coordinates."""
    if not coords or len(coords) < 3:
        return 0.0
    n = len(coords)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        lat1, lng1 = coords[i]
        lat2, lng2 = coords[j]
        area += lng1 * lat2
        area -= lng2 * lat1
    area = abs(area) / 2.0
    km_per_deg_lat = 111.32
    avg_lat = sum(c[0] for c in coords) / n
    km_per_deg_lng = 111.32 * math.cos(math.radians(avg_lat))
    area_sq_km = area * km_per_deg_lat * km_per_deg_lng
    return round(area_sq_km, 4)


@settlement_bp.route("/settlements", methods=["GET"])
@login_required
def get_settlements():
    conn = get_db()

    search = request.args.get("search", "").strip()
    risk_level = request.args.get("risk_level", "").strip()
    status_filter = request.args.get("status", "").strip()
    min_pop = request.args.get("min_pop", type=int)
    max_pop = request.args.get("max_pop", type=int)

    conditions = []
    params = []

    if search:
        conditions.append("s.name ILIKE %s")
        params.append(f"%{search}%")
    if risk_level and risk_level in ("Low", "Medium", "High"):
        conditions.append("s.risk_level = %s")
        params.append(risk_level)
    if status_filter and status_filter in ("Pending", "Approved", "Rejected"):
        conditions.append("s.status = %s")
        params.append(status_filter)
    if min_pop is not None:
        conditions.append("s.population_estimate >= %s")
        params.append(min_pop)
    if max_pop is not None:
        conditions.append("s.population_estimate <= %s")
        params.append(max_pop)

    where = " AND ".join(conditions) if conditions else "1=1"
    query = f"SELECT s.* FROM settlements s WHERE {where} ORDER BY s.created_at DESC"

    rows = _fetchall(conn, query, params)
    conn.close()
    return jsonify([row_to_settlement(r) for r in rows])


@settlement_bp.route("/settlements", methods=["POST"])
@roles_required("Planner", "Authority")
def create_settlement():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400
    name = data.get("name", "").strip()
    polygon_coordinates = data.get("polygon_coordinates")
    population_estimate = data.get("population_estimate")
    risk_level = data.get("risk_level", "Low")
    housing_type = data.get("housing_type", "")
    notes = data.get("notes", "")

    if not name or not polygon_coordinates:
        return jsonify({"error": "Name and coordinates are required"}), 400

    area = compute_polygon_area(polygon_coordinates)
    density = None
    if population_estimate and area > 0:
        density = round(population_estimate / area, 2)

    now = datetime.utcnow().isoformat()
    conn = get_db()
    row = _fetchone(
        conn,
        """INSERT INTO settlements
           (name, polygon_coordinates, population_estimate, risk_level,
            housing_type, notes, area, density, status, created_by, created_at, updated_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Pending', %s, %s, %s)
           RETURNING id""",
        (
            name, json.dumps(polygon_coordinates), population_estimate,
            risk_level, housing_type, notes, area, density,
            session["user_id"], now, now,
        ),
    )
    new_id = row["id"]
    conn.commit()
    conn.close()
    log_action(session["user_id"], "create_settlement", "settlement", new_id, name)
    return jsonify({"success": True, "id": new_id}), 201


@settlement_bp.route("/settlements/<int:settlement_id>", methods=["PUT"])
@roles_required("Planner", "Authority")
def update_settlement(settlement_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400
    conn = get_db()
    row = _fetchone(conn, "SELECT * FROM settlements WHERE id = %s", (settlement_id,))
    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    if session["role"] == "Authority" and row["created_by"] != session["user_id"]:
        conn.close()
        return jsonify({"error": "You can only edit your own settlements"}), 403

    try:
        existing_coords = json.loads(row["polygon_coordinates"])
    except (json.JSONDecodeError, TypeError):
        existing_coords = []

    name = data.get("name", row["name"])
    polygon_coordinates = data.get("polygon_coordinates", existing_coords)
    population_estimate = data.get("population_estimate", row["population_estimate"])
    risk_level = data.get("risk_level", row["risk_level"])
    housing_type = data.get("housing_type", row["housing_type"])
    notes = data.get("notes", row["notes"])

    area = compute_polygon_area(polygon_coordinates)
    density = None
    if population_estimate and area > 0:
        density = round(population_estimate / area, 2)

    now = datetime.utcnow().isoformat()
    _execute(
        conn,
        """UPDATE settlements SET
            name=%s, polygon_coordinates=%s, population_estimate=%s,
            risk_level=%s, housing_type=%s, notes=%s, area=%s, density=%s, updated_at=%s
           WHERE id=%s""",
        (
            name, json.dumps(polygon_coordinates), population_estimate,
            risk_level, housing_type, notes, area, density, now, settlement_id,
        ),
    )
    conn.commit()
    conn.close()
    log_action(session["user_id"], "update_settlement", "settlement", settlement_id, name)
    return jsonify({"success": True})


@settlement_bp.route("/settlements/<int:settlement_id>/status", methods=["PUT"])
@roles_required("Planner", "Authority")
def update_settlement_status(settlement_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400
    status = data.get("status", "").strip()
    if status not in ("Approved", "Rejected", "Pending"):
        return jsonify({"error": "Invalid status"}), 400
    conn = get_db()
    _execute(
        conn,
        "UPDATE settlements SET status=%s, updated_at=%s WHERE id=%s",
        (status, datetime.utcnow().isoformat(), settlement_id),
    )
    conn.commit()
    conn.close()
    log_action(session["user_id"], f"settlement_{status.lower()}", "settlement", settlement_id)
    return jsonify({"success": True})


@settlement_bp.route("/settlements/<int:settlement_id>", methods=["DELETE"])
@roles_required("Planner", "Authority")
def delete_settlement(settlement_id):
    conn = get_db()
    row = _fetchone(conn, "SELECT * FROM settlements WHERE id=%s", (settlement_id,))
    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    if session["role"] == "Authority" and row["created_by"] != session["user_id"]:
        conn.close()
        return jsonify({"error": "You can only delete your own settlements"}), 403

    _execute(conn, "DELETE FROM settlements WHERE id = %s", (settlement_id,))
    conn.commit()
    conn.close()
    log_action(session["user_id"], "delete_settlement", "settlement", settlement_id, row["name"])
    return jsonify({"success": True})

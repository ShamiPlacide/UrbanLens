import io
import csv
from datetime import datetime

from flask import Blueprint, jsonify, session, make_response

from urbanlens.auth import login_required
from urbanlens.database import get_db

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics/stats", methods=["GET"])
@login_required
def get_stats():
    conn = get_db()

    # Settlement stats
    settlements = conn.execute("SELECT * FROM settlements").fetchall()
    total_settlements = len(settlements)
    total_pop = sum(r["population_estimate"] or 0 for r in settlements)
    total_area = sum(r["area"] or 0 for r in settlements)
    avg_density = round(total_pop / total_area, 2) if total_area > 0 else 0

    risk_counts = {"Low": 0, "Medium": 0, "High": 0}
    status_counts = {"Pending": 0, "Approved": 0, "Rejected": 0}
    for r in settlements:
        risk_counts[r["risk_level"]] = risk_counts.get(r["risk_level"], 0) + 1
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1

    # Infrastructure stats
    infra_rows = conn.execute("SELECT type, condition FROM infrastructure").fetchall()
    total_infra = len(infra_rows)
    infra_by_type = {}
    condition_counts = {"Good": 0, "Fair": 0, "Poor": 0, "Critical": 0}
    for r in infra_rows:
        infra_by_type[r["type"]] = infra_by_type.get(r["type"], 0) + 1
        if r["condition"]:
            condition_counts[r["condition"]] = condition_counts.get(r["condition"], 0) + 1

    conn.close()

    return jsonify({
        "settlements": {
            "total": total_settlements,
            "total_population": total_pop,
            "total_area_km2": round(total_area, 4),
            "avg_density": avg_density,
            "by_risk": risk_counts,
            "by_status": status_counts,
        },
        "infrastructure": {
            "total": total_infra,
            "by_type": infra_by_type,
            "by_condition": condition_counts,
        },
    })


@analytics_bp.route("/analytics/report/csv", methods=["GET"])
@login_required
def export_csv():
    conn = get_db()

    settlements = conn.execute("""
        SELECT s.*, u.name as creator_name
        FROM settlements s
        LEFT JOIN users u ON s.created_by = u.id
        ORDER BY s.created_at DESC
    """).fetchall()

    infra = conn.execute("""
        SELECT i.*, s.name as settlement_name
        FROM infrastructure i
        LEFT JOIN settlements s ON i.settlement_id = s.id
        ORDER BY i.created_at DESC
    """).fetchall()

    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    # Settlements section
    writer.writerow(["=== URBANLENS PLANNING REPORT ==="])
    writer.writerow([f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"])
    writer.writerow([])
    writer.writerow(["=== SETTLEMENTS ==="])
    writer.writerow(["ID", "Name", "Status", "Risk Level", "Population",
                      "Area (km2)", "Density (/km2)", "Housing Type",
                      "Created By", "Created At", "Notes"])
    for s in settlements:
        writer.writerow([
            s["id"], s["name"], s["status"], s["risk_level"],
            s["population_estimate"] or "", s["area"] or "",
            s["density"] or "", s["housing_type"] or "",
            s["creator_name"] or "", s["created_at"] or "",
            s["notes"] or ""
        ])

    writer.writerow([])
    writer.writerow(["=== INFRASTRUCTURE ==="])
    writer.writerow(["ID", "Settlement", "Type", "Name", "Geometry",
                      "Condition", "Created At", "Notes"])
    for i in infra:
        writer.writerow([
            i["id"], i["settlement_name"] or "", i["type"], i["name"],
            i["geometry_type"], i["condition"] or "",
            i["created_at"] or "", i["notes"] or ""
        ])

    # Summary section
    writer.writerow([])
    writer.writerow(["=== SUMMARY ==="])
    total_pop = sum(s["population_estimate"] or 0 for s in settlements)
    total_area = sum(s["area"] or 0 for s in settlements)
    writer.writerow(["Total Settlements", len(settlements)])
    writer.writerow(["Total Population", total_pop])
    writer.writerow(["Total Area (km2)", round(total_area, 4)])
    writer.writerow(["Total Infrastructure", len(infra)])

    resp = make_response(output.getvalue())
    resp.headers["Content-Type"] = "text/csv"
    resp.headers["Content-Disposition"] = \
        f"attachment; filename=urbanlens_report_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return resp

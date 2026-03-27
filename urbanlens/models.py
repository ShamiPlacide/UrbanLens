import json


def row_to_settlement(row):
    try:
        coords = json.loads(row["polygon_coordinates"])
    except (json.JSONDecodeError, TypeError):
        coords = []
    return {
        "id": row["id"],
        "name": row["name"],
        "polygon_coordinates": coords,
        "population_estimate": row["population_estimate"],
        "risk_level": row["risk_level"],
        "housing_type": row["housing_type"],
        "notes": row["notes"],
        "area": row["area"],
        "density": row["density"],
        "status": row["status"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def row_to_infrastructure(row):
    try:
        coords = json.loads(row["coordinates"])
    except (json.JSONDecodeError, TypeError):
        coords = []
    return {
        "id": row["id"],
        "settlement_id": row["settlement_id"],
        "type": row["type"],
        "name": row["name"],
        "geometry_type": row["geometry_type"],
        "coordinates": coords,
        "condition": row["condition"],
        "notes": row["notes"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }

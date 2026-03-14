# 🗺 UrbanLens — Kigali Settlement Mapping

UrbanLens is an MVP web application for urban planners to digitally map and track informal settlements in Kigali.

## Features
- 🔐 Login-protected dashboard
- 🗺 Interactive Leaflet map centered on Kigali
- ✏ Draw polygon boundaries for settlements
- 📋 Enter name, population estimate, and risk level
- 💾 Save to SQLite database via Flask REST API
- 👁 View all saved settlements as polygons with popups
- 🗑 Delete settlements from sidebar

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the server
```bash
python app.py
```

### 3. Open in browser
```
http://localhost:5000
```

### 4. Login credentials
- **Email:** admin@urbanlens.com
- **Password:** admin123

## Tech Stack
- **Frontend:** HTML, CSS, JavaScript, Leaflet.js, Leaflet.draw
- **Backend:** Python, Flask
- **Database:** SQLite (auto-created as `urbanlens.db`)

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/login` | Authenticate user |
| POST | `/logout` | End session |
| GET | `/settlements` | Fetch all settlements |
| POST | `/settlements` | Create settlement |
| DELETE | `/settlements/<id>` | Delete settlement |

## Data Model
```json
{
  "id": 1,
  "name": "Nyamirambo North",
  "polygon_coordinates": [[-1.944, 30.062], ...],
  "population_estimate": 4500,
  "risk_level": "High",
  "created_at": "2024-01-15T10:30:00"
}
```

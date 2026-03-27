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

# UrbanLens — Kigali Settlement Mapping Platform

A web application for mapping, managing, and monitoring informal settlements in Kigali, Rwanda. Built with Flask, SQLite, and Leaflet.js.

## Prerequisites

- Python 3.8+
- pip

## Setup & Run

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ShamiPlacide/UrbanLens.git
   cd UrbanLens

Install dependencies:

pip install flask bcrypt

Run the app:

python run.py

Open in browser:

http://localhost:5000

Demo Accounts
Role	Email	Password	Permissions
Planner	admin@urbanlens.com	admin123	Full admin: users, audit log, all settlements
Authority	authority@urbanlens.com	auth123	CRUD own settlements, approve/reject, add infra
Researcher	researcher@urbanlens.com	research123	Read-only view of all settlements (inc. pending)
Project Structure
UrbanLens/
├── run.py                          # Entry point
├── config.py                       # Configuration (env vars)
├── urbanlens/
│   ├── __init__.py                 # Flask app factory
│   ├── auth.py                     # login_required & roles_required decorators
│   ├── database.py                 # SQLite schema, migrations, seed data
│   ├── models.py                   # Row serializers
│   ├── routes/
│   │   ├── __init__.py             # Blueprint registration
│   │   ├── auth_routes.py          # Login, logout, profile
│   │   ├── settlement_routes.py    # Settlement CRUD + search/filter
│   │   ├── infrastructure_routes.py# Infrastructure CRUD
│   │   ├── user_routes.py          # User management (Planner only)
│   │   └── audit_routes.py         # Audit log (Planner only)
│   ├── static/
│   │   ├── css/main.css            # All styles
│   │   └── js/
│   │       ├── app.js              # Auth, role UI, utilities
│   │       ├── map.js              # Leaflet map + draw controls
│   │       ├── settlements.js      # Settlement CRUD frontend
│   │       ├── infrastructure.js   # Infrastructure CRUD frontend
│   │       ├── layers.js           # Map layer toggles
│   │       ├── users.js            # User management panel
│   │       └── audit.js            # Audit log panel
│   └── templates/
│       └── index.html              # Single-page app template

Features
Interactive Map — Draw settlement polygons on a dark-themed Leaflet map centered on Kigali
Settlement Management — Create, edit, delete settlements with population, risk level, housing type, and notes
Approval Workflow — Settlements start as Pending; Planners and Authorities can approve or reject
Infrastructure Mapping — Map roads, water points, sanitation, schools, health centers as Points, Lines, or Polygons
Search & Filter — Filter settlements by name, risk level, status, and population range
Data Layers — Toggle visibility of settlements and each infrastructure type independently
User Management — Planner can create/delete users and assign roles
Audit Log — All actions (login, create, update, delete, approve) are logged
Profile Editing — Users can update their display name and password
Role-Based Access Control — Three roles with different permissions (see table above)
Auto Area & Density — Polygon area (km²) and population density calculated automatically
Environment Variables (optional)
Variable	Default	Description
SECRET_KEY	urbanlens_dev_secret_2024	Flask session secret
DB_PATH	urbanlens.db	SQLite database path
FLASK_DEBUG	false	Enable debug mode
Database
SQLite is used with automatic schema creation on first run. If upgrading from an older version, missing columns are added automatically via migrations. Delete urbanlens.db to start fresh with seeded demo users.

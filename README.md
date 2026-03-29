# UrbanLens — Kigali Settlement Mapping

Web application for urban planners to digitally map and track informal settlements in Kigali.

## Features
- Role-based access (Planner, Authority, Researcher)
- Interactive Leaflet map with polygon drawing
- Settlement CRUD with approval workflow
- Infrastructure mapping (roads, water, schools, etc.)
- Analytics dashboard with CSV/print export
- Audit log for accountability

## Quick Start (Local Development)

### Prerequisites
- Python 3.10+
- PostgreSQL running locally

### 1. Create a PostgreSQL database
- bash
- createdb urbanlens

### 2. Install dependencies
```pip install -r requirements.txt```

### 3. Set environment variables
- export DATABASE_URL=postgresql://localhost:5432/urbanlens
- export SECRET_KEY=your-secret-key

### 4. Run the server
- python run.py

### 5. Open in browser
http://localhost:5000

## Demo accounts
- Role	Email	Password
- Planner (Admin)	admin@urbanlens.com	admin123
- Authority	authority@urbanlens.com	auth123
- Researcher	researcher@urbanlens.com	research123

## Deployment (Render)
1. Push code to GitHub
2. Go to render.com and connect your GitHub repo
3. Click New > Blueprint and select this repo — render.yaml auto-configures:
  - A free PostgreSQL database
  - A web service with gunicorn
  - Auto-generated SECRET_KEY
4. Render auto-deploys on every push to main

### CI/CD
## GitHub Actions runs on every push:

- Flake8 linting
- Integration tests against a PostgreSQL service container
- Tests login, settlements, analytics, and infrastructure endpoints
## Tech Stack
- Frontend: HTML, CSS, JavaScript, Leaflet.js, Leaflet.draw
- Backend: Python, Flask, Gunicorn
- Database: PostgreSQL (psycopg2)
- CI/CD: GitHub Actions
- Hosting: Render

---

import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "urbanlens_dev_secret_2024")
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/urbanlens")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")

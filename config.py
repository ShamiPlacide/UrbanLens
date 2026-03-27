import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "urbanlens_dev_secret_2024")
    DB_PATH = os.environ.get("DB_PATH", "urbanlens.db")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")

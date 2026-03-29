from flask import Flask
from config import Config
from urbanlens.database import init_db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.secret_key = config_class.SECRET_KEY
    app.config["DATABASE_URL"] = config_class.DATABASE_URL
    app.config["DEBUG"] = config_class.DEBUG

    from urbanlens.routes import register_blueprints
    register_blueprints(app)

    with app.app_context():
        init_db(app.config["DATABASE_URL"])

    return app

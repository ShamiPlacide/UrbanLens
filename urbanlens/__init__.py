from flask import Flask
from config import Config
from urbanlens.database import init_db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.secret_key = config_class.SECRET_KEY
    app.config["DB_PATH"] = config_class.DB_PATH
    app.config["DEBUG"] = config_class.DEBUG

    from urbanlens.routes import register_blueprints
    register_blueprints(app)

    with app.app_context():
        init_db(app.config["DB_PATH"])

    return app

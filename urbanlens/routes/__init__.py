from urbanlens.routes.auth_routes import auth_bp
from urbanlens.routes.settlement_routes import settlement_bp
from urbanlens.routes.user_routes import user_bp
from urbanlens.routes.audit_routes import audit_bp
from urbanlens.routes.infrastructure_routes import infrastructure_bp
from urbanlens.routes.analytics_routes import analytics_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(settlement_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(infrastructure_bp)
    app.register_blueprint(analytics_bp)

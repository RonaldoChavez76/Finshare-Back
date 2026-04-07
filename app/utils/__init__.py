from flask import Flask, jsonify
from flask_cors import CORS
from app.config.settings import active_config
# Quitamos los imports de blueprints de aquí arriba

def create_app() -> Flask:
    app = Flask(__name__)
    app.config["DEBUG"] = active_config.DEBUG

    CORS(app)

    # IMPORTANTE: Los importamos AQUÍ ADENTRO. 
    # Esto hace que Flask no los busque hasta que la app ya esté lista.
    from app.routes.auth_routes import auth_bp
    from app.routes.group_routes import groups_bp
    from app.routes.expense_routes import expenses_bp
    from app.routes.transaction_routes import transactions_bp

    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(transactions_bp)

    # Health check
    @app.get("/api/health")
    def health():
        return jsonify({
            "status": "ok", 
            "app": "FinShare Analytics",
            "environment": "development" if active_config.DEBUG else "production"
        })

    # Handlers globales (estos están perfectos)
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Ruta no encontrada"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "error": "Método no permitido"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"success": False, "error": "Error interno del servidor"}), 500

    return app
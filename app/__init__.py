from flask import Flask
from flask_cors import CORS
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Inicializar la base de datos globalmente
db = None

def create_app():
    global db
    
    app = Flask(__name__)
    
    # Habilitar CORS para que React pueda consumir la API sin bloqueos
    CORS(app)
    
    # Configuración de MongoDB
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    client = MongoClient(mongo_uri)
    db = client.finshare_db # Nombre de tu base de datos
    
    # Aquí registraremos los controladores (Blueprints) más adelante
    # from app.controllers.usuario_controller import usuario_bp
    # app.register_blueprint(usuario_bp, url_prefix='/api/usuarios')
    
   #1. Autenticación (Pública)
    from app.routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # 2. Grupos (Unificados)
    from app.routes.group_routes import groups_bp
    app.register_blueprint(groups_bp, url_prefix='/api/groups')
    
    # 3. Gastos (Corregido el typo de 'expanse')
    from app.routes.expense_routes import expenses_bp
    app.register_blueprint(expenses_bp)

    # 4. Versiones en Español (Si las vas a mantener para tu compañero)
    from app.controllers.gasto_controller import gasto_bp
    app.register_blueprint(gasto_bp, url_prefix='/api/gastos')
    
    from app.controllers.grupo_controller import grupo_bp
    app.register_blueprint(grupo_bp, url_prefix='/api/grupos_es') # Prefijo diferente para evitar choque

    # 5. Análisis de Riesgo Financiero
    from app.routes.risk_routes import risk_bp
    app.register_blueprint(risk_bp, url_prefix='/api/risk')

    # 6. Simulación de Escenarios
    from app.routes.simulation_routes import simulations_bp
    app.register_blueprint(simulations_bp, url_prefix='/api/simulations')

    # 7. Dashboard / Visualización
    from app.routes.dashboard_routes import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

    # 8. Transacciones Personales
    from app.routes.transaction_routes import transactions_bp
    app.register_blueprint(transactions_bp)
    
    @app.route('/')
    def index():
        return {"mensaje": "API de FinShare Analytics funcionando correctamente"}
        
    return app
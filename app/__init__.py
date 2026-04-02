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
    
    @app.route('/')
    def index():
        return {"mensaje": "API de FinShare Analytics funcionando correctamente"}
        
    return app
from flask import Flask
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config
from .database import init_db, db

# Initialisation des extensions
jwt = JWTManager()
api = Api()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)

    CORS(app)

    # On initialise les extensions
    init_db(app)
    jwt.init_app(app)
    api.init_app(app)

    # On importe et enregistre les ressources API
    from api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/')
    def home():
        return "Welcome to the API!"

    return app

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'datas/recom-films.py'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Importez vos modèles ici
from app import models

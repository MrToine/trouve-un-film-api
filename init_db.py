from app import create_app
from app.database import db

app = create_app()

with app.app_context():
    db.create_all()
    print("Base de données initialisée.")
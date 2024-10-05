from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    db.init_app(app)
    migrate.init_app(app, db)

    # Importer les modèles ici pour s'assurer qu'ils sont chargés avant la création des tables
    from app.models import Movie, Genre, Participant, MovieParticipant, MovieGenre, User

    # Créer les tables dans un contexte d'application
    with app.app_context():
        db.create_all()

def get_db():
    return db.session
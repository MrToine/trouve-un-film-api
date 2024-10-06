from app import create_app
from app.database import db
from flask_migrate import Migrate
from app.models import Participant, User, Movie, Genre, Like, Post, Profile
from app.models.relations import MovieGenre, MovieParticipant
from app.reco import load_data  # Assurez-vous que c'est le bon chemin

app = create_app()
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Profile': Profile,
        'Like': Like,
        'Movie': Movie,
        'Genre': Genre,
        'Participant': Participant,
        'MovieGenre': MovieGenre,
        'MovieParticipant': MovieParticipant,
    	'Post': Post
    }

def print_progress(progress, message):
    print(f"{progress}% - {message}")

with app.app_context():
    print("Loading data on startup...")
    load_data(progress_callback=print_progress)
    print("Data loaded successfully.")

if __name__ == '__main__':
    print("Starting the application...")
    print("Available routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule}")
    
    app.run(debug=True)

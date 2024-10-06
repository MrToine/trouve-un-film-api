from flask import Blueprint, request, jsonify, Response, redirect, url_for
from flask_restful import Api
from resources.MovieResource import MovieResource, MovieCountResource, MoviesByDuration, MoviesByGenre, MoviesByLikes, MoviesByYear, moviesByActors, moviesByRealisator
from resources.GenreResource import GenreResource, GenreCountResource, GenreMoviesResource
from resources.RealisatorResource import RealisatorMoviesLiked, RealisatorMoviesLikedPerYear, RealisatorMoviesResource, RealisatorResource, RealisatorCountResource
from resources.ActorResource import ActorMoviesLiked, ActorMoviesLikedPerYear, ActorMoviesResource, ActorResource, ActorCountResource
from resources.UserResource import UserResource
from resources.AuthResource import AuthResource
from resources.UserProfileResource import UserProfileResource
from resources.LikeResource import LikeResource
from resources.PostResource import PostResource
from app.reco import content_based_recommendations, collaborative_filtering_recommendations, hybrid_recommendations
import scripts.scrapper as scrapper_module
import scripts.create_datas_movies as create_datas_movies
import time
import queue
import threading
import json
import os

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

maintenance = False

scrapping_state = {
    'is_running': False,
    'progress': 0,
    'messages': [],
    'last_message': 0
}

SCRAPING_STATE_FILE = 'scraping_state.json'

message_queue = queue.Queue()

# Middleware pour rediriger les requêtes en mode maintenance
@api_bp.before_request
def check_for_maintenance():
    global maintenance
    if maintenance and request.path != url_for('api.get_maintenance') and request.path != url_for('api.set_maintenance'):
        return redirect(url_for('api.get_maintenance'))

# Enregistrement des ressources
api.add_resource(MovieResource, '/movies', '/movies/<int:movie_id>')
api.add_resource(MovieCountResource, '/movies/count')
api.add_resource(GenreResource, '/genres')
api.add_resource(GenreCountResource, '/genres/count')
api.add_resource(GenreMoviesResource, '/genres/movies/count/', '/genres/movies/count/<int:genre_id>')
api.add_resource(RealisatorResource, '/participants/realisators', '/participants/realisators/<int:real_id>')
api.add_resource(RealisatorCountResource, '/participants/realisators/count')
api.add_resource(ActorResource, '/participants/actors', '/participants/actors/<int:actor_id>')
api.add_resource(ActorCountResource, '/participants/actors/count')

api.add_resource(PostResource, '/posts', '/posts/<int:user_id>')

api.add_resource(UserResource, '/users', '/users/<int:user_id>')
api.add_resource(AuthResource, '/users/login')
api.add_resource(UserProfileResource, '/users/profile', '/users/profile/<int:user_id>', methods=['GET', 'PATCH'])

api.add_resource(LikeResource, '/likes', '/likes/<int:user_id>')

# Stats
api.add_resource(MoviesByLikes, '/likes/sorted', '/likes/sorted/<int:nb_sorted>')
api.add_resource(MoviesByYear, '/movies/year', '/movies/year/<int:year>')
api.add_resource(MoviesByDuration, '/movies/duration')
api.add_resource(MoviesByGenre, '/movies/genre')
api.add_resource(moviesByRealisator, '/movies/realisator')
api.add_resource(moviesByActors, '/movies/actors')

api.add_resource(RealisatorMoviesResource, '/participants/realisators/movies', 'realisators/<int:real_id>/movies')
api.add_resource(RealisatorMoviesLiked, '/participants/realisators/movies/liked')
api.add_resource(RealisatorMoviesLikedPerYear, '/participants/realisators/movies/liked/year')

api.add_resource(ActorMoviesResource, '/participants/actors/movies', 'realisators/<int:real_id>/movies')
api.add_resource(ActorMoviesLiked, '/participants/actors/movies/liked')
api.add_resource(ActorMoviesLikedPerYear, '/participants/actors/movies/liked/year')

@api_bp.route('')
def hello():
    return {"message": "Hello from the API!"}

@api_bp.route('/scripts/maintenance')
def set_maintenance():
    global maintenance
    maintenance = not maintenance
    return jsonify({"maintenance": maintenance})

@api_bp.route('/maintenance', methods=['GET'])
def get_maintenance():
    if maintenance:
        return jsonify({"message": "maintenance on"}), 503
    else:
        return jsonify({"message": "maintenance off"}), 200

@api_bp.route('/recommendations/hybride/<int:user_id>')
def hybrid_reco(user_id):
    top_n = int(request.args.get('top_n', 10))
    genres = request.args.get('genres')
    realisator = request.args.get('realisator')
    actors = request.args.get('actors')
    try:
        reco = hybrid_recommendations(user_id, genres, realisator, actors, top_n)
        return jsonify(reco)
    except TimeoutError:
        return jsonify({"error": "Data is still loading, please try again later"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/recommendations/simple')
def reco():
    top_n = int(request.args.get('top_n', 10))
    genres = request.args.get('genres')
    realisator = request.args.get('realisator')
    actors = request.args.get('actors')
    try:
        reco = content_based_recommendations(genres, realisator, actors, top_n)
        print(f"genres: {genres}, realisator: {realisator}, actors: {actors}")
        return jsonify(reco)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

def save_scraping_state():
    with open(SCRAPING_STATE_FILE, 'w') as f:
        json.dump(scrapping_state, f)

def load_scraping_state():
    global scrapping_state
    if os.path.exists(SCRAPING_STATE_FILE):
        with open(SCRAPING_STATE_FILE, 'r') as f:
            scrapping_state = json.load(f)
    else:
        scrapping_state = {
            'is_running': False,
            'progress': 0,
            'messages': [],
            'last_message': 0
        }

@api_bp.route('/scripts/refresh_db')
def refresh():
    secret_key = "8363bd887ab0f1d7277c074egzr5re4ecze39ba5b55369978b46476dbe"
    key = request.args.get('key')

    if key != secret_key:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Lancer le script de rafraichissement de la base de données dans un thread séparé
    threading.Thread(target=create_datas_movies.refresh(), daemon=True).start()


@api_bp.route('/scripts/scrapper')
def scrapper():
    secret_key = "8363bd887ab0f1d7277c07165291af5c027688c4239ba5b55369978b46476dbe"
    key = request.args.get('key')
    last_id = int(request.args.get('last_id', 0,))

    if key != secret_key:
        return jsonify({"error": "Unauthorized"}), 401
    
    message_queue = queue.Queue()
        
    def callback(message):
        global scrapping_state
        scrapping_state['last_message'] += 1
        message_data = {
            'id': scrapping_state['last_message'],
            'content': message['text'],
            'status': message['status'],
            'progress': message['progress']
        }
        scrapping_state['messages'].append(message_data)
        scrapping_state['progress'] = message['progress']
        message_queue.put(message_data)
        save_scraping_state()

    def generate_messages():
        global scrapping_state
        load_scraping_state()
        if not scrapping_state['is_running']:
            scrapping_state['is_running'] = True
            scrapping_state = {
                'is_running': False,
                'progress': 0,
                'messages': [],
                'last_message': 0,
                'recent_messages': scrapping_state['messages'][-10:]
            }
            # Lancer le scraping dans un thread séparé
            threading.Thread(target=scrapper_module.main, args=(callback,), daemon=True).start()
        
        while True:
            if not message_queue.empty():
                message = message_queue.get()
                yield f"data: {json.dumps({'message': message, 'progress': scrapping_state['progress']})}\n\n"
            else:
                yield f"data: {json.dumps({'progress': scrapping_state['progress']})}\n\n"
            time.sleep(2)
            save_scraping_state()

    return Response(generate_messages(), mimetype='text/event-stream')

@api_bp.route('/scripts/scrapper/status')
def scrapper_status():
    load_scraping_state()
    return jsonify({
        'is_running': scrapping_state['is_running'],
        'progress': scrapping_state['progress'],
        'last_message': scrapping_state['last_message']
    })

@api_bp.route('/scripts/scrapper/reset', methods=['POST'])
def reset_scrapper():
    global scrapping_state
    scrapping_state = {
        'is_running': False,
        'progress': 0,
        'messages': [],
        'last_message': 0,
        'recent_messages': scrapping_state['messages'][-10:]
    }
    save_scraping_state()
    return jsonify({"message": "Scrapper reset successfully"})
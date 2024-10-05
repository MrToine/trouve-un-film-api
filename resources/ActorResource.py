from flask_restful import Resource
from flask_jwt_extended import jwt_required
from sqlalchemy.orm import joinedload
from app.models import Like
from app.models import Participant
from app.models import Movie
from sqlalchemy import func
from app.database import db

class ActorResource(Resource):
    def get(self, real_id=None):
        if real_id:
            actor = Participant.query.options(joinedload('movies')).filter_by(id=real_id, isActor=True).first()
            if actor:
                return {
                    'id': actor.id,
                    'name': actor.name,
                    'total_movies': len(actor.movies),
                }
        else:
            # On récupère les actors dans Participants > isactor = True
            actors = Participant.query.options(joinedload('movies')).filter_by(isActor=True).all()
            return [{
                'id': actor.id,
                'name': actor.name,
                'total_movies': len(actor.movies),
            } for actor in actors]

class ActorCountResource(Resource):
    def get(self):
        return {'count': Participant.query.filter_by(isActor=True).count()}
    
class ActorMoviesResource(Resource):
    def get(self, real_id=None):
        # On récupoère le nombre de films pour un acteur. Si aucun acteur n'est mentionné, on renvoie les 10 acteur avec le plus de films
        if real_id:
            actor = Participant.query.options(joinedload('movies')).filter_by(id=real_id, isActor=True).first()
            if actor:
                return {
                    'id': actor.id,
                    'name': actor.name,
                    'total_movies': len(actor.movies),
                    'movies': [movie.title for movie in actor.movies]
                }
        else:
            actors = Participant.query.options(joinedload('movies')).filter_by(isActor=True).all()
            actors = sorted(actors, key=lambda x: len(x.movies), reverse=True)
            return [{
                'id': actor.id,
                'name': actor.name,
                'total_movies': len(actor.movies),
            } for actor in actors[:10]]

class ActorMoviesLiked(Resource):
    def get(self):
        # Sous-requête pour compter les likes par film
        likes_count = db.session.query(
            Like.movie_id,
            func.count(Like.id).label('likes_count')
        ).filter(Like.like == True).group_by(Like.movie_id).subquery()

        # Requête principale
        actors = db.session.query(
            Participant,
            func.sum(likes_count.c.likes_count).label('total_likes')
        ).join(Participant.movies).outerjoin(
            likes_count,
            Movie.id == likes_count.c.movie_id
        ).filter(Participant.isActor == True).group_by(
            Participant.id
        ).order_by(func.sum(likes_count.c.likes_count).desc()).limit(10).all()

        return [{
            'id': actor.id,
            'name': actor.name,
            'total_likes': int(total_likes) if total_likes else 0,
        } for actor, total_likes in actors]

class ActorMoviesLikedPerYear(Resource):
    def get(self):
        # On récupère le nombre de likes par année pour les acteurs pour les 10 dernières années
        likes_count = db.session.query(
            Like.movie_id,
            func.count(Like.id).label('likes_count'),
            Movie.year
        ).join(Like.movie).filter(Like.like == True).group_by(Like.movie_id, Movie.year).subquery()

        actors = db.session.query(
            Participant,
            func.sum(likes_count.c.likes_count).label('total_likes'),
            likes_count.c.year
        ).join(Participant.movies).outerjoin(
            likes_count,
            Movie.id == likes_count.c.movie_id
        ).filter(Participant.isActor == True).group_by(
            Participant.id, likes_count.c.year
        ).order_by(func.sum(likes_count.c.likes_count).desc()).limit(10).all()

        return [{
            'id': actor.id,
            'name': actor.name,
            'total_likes': int(total_likes) if total_likes else 0,
            'year': year
        } for actor, total_likes, year in actors]
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from sqlalchemy.orm import joinedload
from app.models import Like
from app.models import Participant
from app.models import Movie
from sqlalchemy import func
from app.database import db

class RealisatorResource(Resource):
    def get(self, real_id=None):
        if real_id:
            realisator = Participant.query.options(joinedload('movies')).filter_by(id=real_id, isRealisator=True).first()
            if realisator:
                return {
                    'id': realisator.id,
                    'name': realisator.name,
                    'total_movies': len(realisator.movies),
                }
        else:
            # On récupère les realisators dans Participants > isRealisator = True
            realisators = Participant.query.options(joinedload('movies')).filter_by(isRealisator=True).all()
            return [{
                'id': realisator.id,
                'name': realisator.name,
                'total_movies': len(realisator.movies),
            } for realisator in realisators]

class RealisatorCountResource(Resource):
    def get(self):
        return {'count': Participant.query.filter_by(isRealisator=True).count()}
    
class RealisatorMoviesResource(Resource):
    def get(self, real_id=None):
        # On récupoère le nombre de films pour un realisateur. Si aucun realisateur n'est mentionné, on renvoie les 10 realisateur avec le plus de films
        if real_id:
            realisator = Participant.query.options(joinedload('movies')).filter_by(id=real_id, isRealisator=True).first()
            if realisator:
                return {
                    'id': realisator.id,
                    'name': realisator.name,
                    'total_movies': len(realisator.movies),
                    'movies': [movie.title for movie in realisator.movies]
                }
        else:
            realisators = Participant.query.options(joinedload('movies')).filter_by(isRealisator=True).all()
            realisators = sorted(realisators, key=lambda x: len(x.movies), reverse=True)
            return [{
                'id': realisator.id,
                'name': realisator.name,
                'total_movies': len(realisator.movies),
            } for realisator in realisators[:10]]

class RealisatorMoviesLiked(Resource):
    def get(self):
        # Sous-requête pour compter les likes par film
        likes_count = db.session.query(
            Like.movie_id,
            func.count(Like.id).label('likes_count')
        ).filter(Like.like == True).group_by(Like.movie_id).subquery()

        # Requête principale
        realisators = db.session.query(
            Participant,
            func.sum(likes_count.c.likes_count).label('total_likes')
        ).join(Participant.movies).outerjoin(
            likes_count,
            Movie.id == likes_count.c.movie_id
        ).filter(Participant.isRealisator == True).group_by(
            Participant.id
        ).order_by(func.sum(likes_count.c.likes_count).desc()).limit(10).all()

        return [{
            'id': realisator.id,
            'name': realisator.name,
            'total_likes': int(total_likes) if total_likes else 0,
        } for realisator, total_likes in realisators]

class RealisatorMoviesLikedPerYear(Resource):
    def get(self):
        # On récupère le nombre de likes par année pour les realisateurs pour les 10 dernières années
        likes_count = db.session.query(
            Like.movie_id,
            func.count(Like.id).label('likes_count'),
            Movie.year
        ).join(Like.movie).filter(Like.like == True).group_by(Like.movie_id, Movie.year).subquery()

        realisators = db.session.query(
            Participant,
            func.sum(likes_count.c.likes_count).label('total_likes'),
            likes_count.c.year
        ).join(Participant.movies).outerjoin(
            likes_count,
            Movie.id == likes_count.c.movie_id
        ).filter(Participant.isRealisator == True).group_by(
            Participant.id, likes_count.c.year
        ).order_by(func.sum(likes_count.c.likes_count).desc()).limit(10).all()

        return [{
            'id': realisator.id,
            'name': realisator.name,
            'total_likes': int(total_likes) if total_likes else 0,
            'year': year
        } for realisator, total_likes, year in realisators]
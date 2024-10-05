from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Movie
from app.database import db

class RecomendationResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        # Algorithme de recommandation
        movies = Movie.query.order_by(db.func.random()).limit(5).all()
        return [{
            'id': movie.id,
            'title': movie.title,
            'author': movie.author,
            'actors': movie.actors,
            'year': movie.year,
            'month': movie.month,
            'day': movie.day,
            'genre': movie.genre
        } for movie in movies]
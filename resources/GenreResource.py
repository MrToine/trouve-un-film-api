from flask_restful import Resource
from flask_jwt_extended import jwt_required
from app.models import Genre

class GenreResource(Resource):
    def get(self):
        genres = Genre.query.all()
        return [{
            'id': genre.id,
            'name': genre.name
        } for genre in genres]

class GenreCountResource(Resource):
    def get(self):
        return {'count': Genre.query.count()}
    
class GenreMoviesResource(Resource):
    def get(self, genre_id=None):
        if genre_id:
            genre = Genre.query.get_or_404(genre_id)
            return {
                'id': genre.id,
                'name': genre.name,
                'total_movies': len(genre.movies),
            }
        else:
            return [{
                'id': genre.id,
                'name': genre.name,
                'movies_count': len(genre.movies)
            } for genre in Genre.query.all()]
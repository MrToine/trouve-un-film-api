from flask_restful import Resource, reqparse
from app.models import Like
from app.database import db

class LikeResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user_id', type=int, required=True)
        parser.add_argument('movie_id', type=int, required=True)
        data = parser.parse_args()
        # On vérifie si l'utilisateur a déjà liké le film
        like = Like.query.filter_by(user_id=data['user_id'], movie_id=data['movie_id']).first()
        # Si le like est à True, on le passe à False
        if like:
            like.like = not like.like
            db.session.commit()
            return {"message": "Like updated"}, 200
        # On crée le like
        like = Like(user_id=data['user_id'], movie_id=data['movie_id'], like=True)
        db.session.add(like)
        db.session.commit()
        return {"message": "Like created"}, 201
    
    def get(self, user_id=None):
        if user_id:
            likes = Like.query.filter_by(user_id=user_id).all()
            return [{
                'movie_id': like.movie_id,
                'like': like.like
            } for like in likes]
        likes = Like.query.all()
        return [{
            'user_id': like.user_id,
            'movie_id': like.movie_id,
            'like': like.like
        } for like in likes]
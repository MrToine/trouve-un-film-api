from flask_restful import Resource, reqparse
from app.models import User
from app.database import db

class UserResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True)
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        data = parser.parse_args()

        # le nom d'utilisateur existe déjà
        if User.query.filter_by(username=data['username']).first() is not None:
            return {'error': 'Username already exists'}, 400

        # si l'email existe déjà
        if User.query.filter_by(email=data['email']).first() is not None:
            return {'error': 'Email already exists'}, 400

        # nouvel utilisateur
        user = User(username=data['username'], email=data['email'])
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()

        return {
            'id': user.id,
            'username': user.username,
            'role': user.role
        }, 201
    
    def get(self, user_id=None):
        if user_id:
            print("user_id")
            user = User.query.get_or_404(user_id)
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                # On récupère les titre de films liker de l'utilisateur
                'likes': [{
                    'status': like.like,
                    'id': like.movie.id,
                    'title': like.movie.title,
                    'poster': like.movie.poster,
                    'year': like.movie.year,
                    'synopsis': like.movie.synopsis,
                    'realisators': [{
                        'name': p.name
                        } for p in like.movie.participants if p.isRealisator],
                    'actors': [{
                        'name': p.name
                        } for p in like.movie.participants if p.isActor],
                    'genres': [{
                        'name': genre.name
                        } for genre in like.movie.genres]
                    } for like in user.likes],
                'role': user.role,
                'posts': [{
                    'id': post.id,
                    'title': post.title,
                    'content': post.content,
                    'created_at': post.created_at.isoformat(),
                    'updated_at': post.updated_at.isoformat(),
                    'user_id': post.user_id,
                    'type': post.type
                } for post in sorted(user.posts, key=lambda post: post.id, reverse=True)]
            }
        users = User.query.all()
        return [{
            'id': user.id,
            'username': user.username,
            'role': user.role,
        } for user in users]
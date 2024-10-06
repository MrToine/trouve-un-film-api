from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Profile
from datetime import datetime

class UserProfileResource(Resource):
    @jwt_required()
    def get(self, user_id=None):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        
        # Comme le profile est une nouvelle fonctionnalité, on ne peut pas garantir que tous les utilisateurs ont un profile. On ajoute donc l'id de l'utilisateur dans le cas où il n'a pas de profile. SI l'id est présent, on ne fait rien.
        if not user.profile:
            user.create_profile()
        
        def serialize_date(date):
            return date.isoformat() if date else None

        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'profile': {
                'first_name': user.profile.first_name,
                'last_name': user.profile.last_name,
                'birth_date': serialize_date(user.profile.birth_date),
                'biography': user.profile.biography,
                'picture': user.profile.picture,
                'active': user.profile.active
            },
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
            'posts': [{
                    'id': post.id,
                    'title': post.title,
                    'content': post.content,
                    'created_at': post.created_at.isoformat(),
                    'updated_at': post.updated_at.isoformat(),
                    'user_id': post.user_id,
                    'type': post.type
                } for post in sorted(user.posts, key=lambda post: post.id, reverse=True)]
        }, 200
    
    @jwt_required()
    def patch(self, user_id):
        user = User.query.get_or_404(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        profile = user.profile
        if not profile:
            profile = Profile(user_id=user.id)

        data = request.get_json()
        print('DATA : ', data)

        # Mettre à jour les champs de l'utilisateur et du profil si présents dans les données
        if 'email' in data:
            user.email = data['email']
        if 'first_name' in data:
            profile.first_name = data['first_name']
        if 'last_name' in data:
            profile.last_name = data['last_name']
        if 'birth_date' in data:
            profile.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        if 'biography' in data:
            profile.biography = data['biography']
        if 'picture' in data:
            profile.picture = data['picture']
        if 'active' in data:
            profile.active = data['active']

        profile.save()
        user.save()

        return {}, 200
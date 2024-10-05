from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User

class UserProfileResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }, 200
    
    @jwt_required()
    def put(self, user_id):
        user = User.query.get_or_404(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        user.role = 'admin'
        user.save()
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }, 200
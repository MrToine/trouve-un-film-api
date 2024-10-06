from functools import wraps
from flask import request
from datetime import datetime
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Post, User
from app.database import db
from datetime import datetime

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or user.role != 'admin':
            return {'message': 'Admin privilege required'}, 403
        return fn(*args, **kwargs)
    return wrapper

class PostResource(Resource):
    def get(self, post_id=None, type=None):
        type = request.args.get('type')

        if type:
            if type == 'info':
                # On récupère uniquement le premier post de type info
                post = Post.query.filter_by(type=type, active=True).first()
                return {
                    'id': post.id,
                    'title': post.title,
                    'content': post.content,
                    'created_at': post.created_at.isoformat(),
                    'updated_at': post.updated_at.isoformat(),
                    'user_id': post.user_id,
                    'type': post.type
                }, 200
            
            posts = Post.query.filter_by(type=type, active=True).all()
            return {
                'posts': [{
                    'id': post.id,
                    'title': post.title,
                    'content': post.content,
                    'created_at': post.created_at.isoformat(),
                    'updated_at': post.updated_at.isoformat(),
                    'user_id': post.user_id,
                    'type': post.type
                } for post in posts]
            }, 200

        if post_id:
            post = Post.query.get_or_404(post_id)
            return {
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'created_at': post.created_at.isoformat(),
                'updated_at': post.updated_at.isoformat(),
                'user_id': post.user_id,
                'type': post.type
            }, 200
        
        posts = Post.query.filter_by(active=True).all()
        return {
            'posts': [{
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'created_at': post.created_at.isoformat(),
                'updated_at': post.updated_at.isoformat(),
                'user_id': post.user_id,
                'type': post.type
            } for post in posts]
        }, 200
    
    @jwt_required()
    def post(self, user_id=None):
        print("POST d'un post")
        user_id = get_jwt_identity()
        post = {
            'title': 'post-' + str(user_id),
            'content': request.json.get('content', ''),
            'user_id': user_id,
            'type': request.json.get('type', 'post'),
            'active': True
        }
        post = Post(**post)
        post.save()
        return {
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'created_at': post.created_at.isoformat(),
            'updated_at': post.updated_at.isoformat(),
            'user_id': post.user_id,
            'type': post.type
        }, 201

    @jwt_required()
    def patch(self):
        type = request.args.get('type')
        if type != 'info':
            return {'message': 'Invalid post type'}, 400

        data = request.get_json()
        content = data.get('content', '')

        info_post = Post.query.filter_by(type='info', active=True).first()
        if info_post:
            info_post.content = content
            info_post.updated_at = datetime.utcnow()
        else:
            info_post = Post(
                title='Info Post',
                content=content,
                user_id=get_jwt_identity(),
                type='info'
            )
            db.session.add(info_post)

        db.session.commit()

        return {
            'id': info_post.id,
            'title': info_post.title,
            'content': info_post.content,
            'created_at': info_post.created_at.isoformat(),
            'updated_at': info_post.updated_at.isoformat(),
            'user_id': info_post.user_id,
            'type': info_post.type
        }, 200

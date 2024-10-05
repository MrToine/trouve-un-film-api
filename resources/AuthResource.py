from flask_restful import Resource, reqparse
from flask_jwt_extended import create_access_token
from app.models import User

class AuthResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('username', type=str, required=True)
        self.parser.add_argument('password', type=str, required=True)
        self.parser.add_argument('email', type=str, required=False)

    def post(self):
        print(f"Tentative de connexion avec {self.parser.parse_args()}")
        data = self.parser.parse_args()
        user = User.query.filter_by(username=data['username']).first()
        if not user or not user.check_password(data['password']):
            return {'error': 'Invalid username or password'}, 401
        access_token = create_access_token(identity=user.id)
        return {'access_token': access_token}, 200
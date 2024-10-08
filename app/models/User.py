from .Profile import Profile
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(50), default='user')

    profile = db.relationship('Profile', back_populates='user', uselist=False)
    posts = db.relationship('Post', back_populates='user')
    likes = db.relationship('Like', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get(self, key, default=None):
        return getattr(self, key, default)

    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def create_profile(self):
        profile = Profile(user_id=self.id)
        profile.save()

    def __repr__(self):
        return '<User {}>'.format(self.username)
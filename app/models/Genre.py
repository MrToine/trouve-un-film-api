from datetime import datetime
from app.database import db

class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), index=True)

    movies = db.relationship('Movie', secondary='movie_genre', back_populates='genres')
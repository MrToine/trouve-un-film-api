from app.database import db

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), index=True)
    duration = db.Column(db.String(10))
    poster = db.Column(db.String(120))
    year = db.Column(db.Integer)
    month = db.Column(db.Integer)
    day = db.Column(db.Integer)
    synopsis = db.Column(db.String(500))
    
    participants = db.relationship('Participant', secondary='movie_participant', back_populates='movies')
    genres = db.relationship('Genre', secondary='movie_genre', back_populates='movies')
    likes = db.relationship('Like', back_populates='movie')
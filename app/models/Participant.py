from app.database import db

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), index=True)
    isActor = db.Column(db.Boolean, default=False)
    isRealisator = db.Column(db.Boolean, default=False)

    movies = db.relationship('Movie', secondary='movie_participant', back_populates='participants')

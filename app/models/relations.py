from app.database import db

class MovieGenre(db.Model):
    __tablename__ = 'movie_genre'
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), primary_key=True)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'), primary_key=True)

class MovieParticipant(db.Model):
    __tablename__ = 'movie_participant'
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'), primary_key=True)
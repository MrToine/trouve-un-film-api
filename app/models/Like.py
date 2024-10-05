from app.database import db

class Like(db.Model):
    __tablename__ = 'like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))
    like = db.Column(db.Boolean)

    user = db.relationship('User', back_populates='likes')
    movie = db.relationship('Movie', back_populates='likes')
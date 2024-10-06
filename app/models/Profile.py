from app import db

class Profile(db.Model):
    __tablename__ = 'profile'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    birth_date = db.Column(db.Date)
    biography = db.Column(db.Text)
    picture = db.Column(db.String(128))
    active = db.Column(db.Boolean, default=False)

    user = db.relationship('User', back_populates='profile')

    def get(self, key, default=None):
        return getattr(self, key, default)

    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()
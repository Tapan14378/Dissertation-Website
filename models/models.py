from flask_login import UserMixin
from extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    requests = db.relationship('Request', backref='user', lazy=True)

    def __init__(self, email, name, password):
        self.email = email
        self.name = name
        self.password = password


class Request(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    type = db.Column(db.String(10), nullable=False)
    start_location = db.Column(db.String(10), nullable=False)
    start_lat = db.Column(db.Float, nullable=True)
    start_long = db.Column(db.Float, nullable=True)
    end_location = db.Column(db.String(10), nullable=False)
    end_lat = db.Column(db.Float, nullable=True)
    end_long = db.Column(db.Float, nullable=True)
    departure_time = db.Column(db.DateTime, nullable=False)
    seats = db.Column(db.Integer, nullable=True)
    pet = db.Column(db.String(10), nullable=False, default='no')
    smoker = db.Column(db.String(10), nullable=False, default='no')
    disable = db.Column(db.String(10), nullable=False, default='no')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

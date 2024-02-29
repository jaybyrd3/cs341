# db_config.py

# Note: for info on how relationships & foreign keys work in Flask-SQLAlchemy,
# see: https://flask-sqlalchemy.palletsprojects.com/en/2.x/models/

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# Define your models here
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    is_active = db.Column(db.Boolean, default=True)
    username = db.Column(db.String(80), unique=False, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password = db.Column(db.String(80), unique=False, nullable=True)
    firstName = db.Column(db.String(80), unique=False, nullable=True)
    lastName = db.Column(db.String(80), unique=False, nullable=True)
    jobTitle = db.Column(db.String(80), unique=False, nullable=True)
    qualifications = db.Column(db.String(80), unique=False, nullable=True)
    # appointments = db.relationship('Slot', backref='user', lazy=True, foreign_keys=[Slot.user_id]) # is a 1-to-many relationship by default
    slots = db.relationship('Slot', backref='slot', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Slot(db.Model):
    __tablename__ = 'slot'
    id = db.Column(db.Integer, primary_key=True)
    starttime = db.Column(db.DateTime, unique=False, nullable=True)
    endtime = db.Column(db.DateTime, unique=False, nullable=True)
    # if user_id == null, then appt slot is open
    client = db.relationship('User', backref='client', lazy=True)
    provider = db.relationship('User', backref='provider', lazy=True)
    # slot will always have a provider
    # provider_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.String(512), unique=False, nullable=True)
    
    def __repr__(self):
	    return f'<Slot {self.time}>'

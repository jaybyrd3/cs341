# db_config.py

# Note: for info on how relationships & foreign keys work in Flask-SQLAlchemy,
# see: https://flask-sqlalchemy.palletsprojects.com/en/2.x/models/

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Define your models here
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=True, nullable=False)
    firstName = db.Column(db.String(80), unique=False, nullable=True)
    lastName = db.Column(db.String(80), unique=False, nullable=True)
    jobTitle = db.Column(db.String(80), unique=False, nullable=True)
    qualifications = db.Column(db.String(80), unique=False, nullable=False)
    appointments = db.relationship('Slot', backref='theUser', lazy=True) # is a 1-to-many relationship by default
    slots = db.relationship('Slot', backref='theProvider', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Slot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, unique=True, nullable=False)
    # if user_id == null, then appt slot is open
    user_id = db.Column(db.Integer, db.ForeignKey('theUser.id'), nullable=True)
    # slot will always have a provider
    provider_id = db.Column(db.Integer, db.ForeignKey('theProvider.id'), nullable=False)
    
    def __repr__(self):
	    return f'<Slot {self.time}>'

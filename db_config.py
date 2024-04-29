# db_config.py

# Note: for info on how relationships & foreign keys work in Flask-SQLAlchemy,
# see: https://flask-sqlalchemy.palletsprojects.com/en/2.x/models/

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import TIMESTAMP
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Define your models here
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(80), unique=False, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), unique=False, nullable=True)
    firstName = db.Column(db.String(80), unique=False, nullable=True)
    lastName = db.Column(db.String(80), unique=False, nullable=True)
    jobTitle = db.Column(db.String(80), unique=False, nullable=True)
    qualifications = db.Column(db.String(80), unique=False, nullable=True)
    notificationCount = db.column(db.Integer, unique=False, nullable=True)
    # appointments = db.relationship('Slot', backref='user', lazy=True, foreign_keys=[Slot.user_id]) # is a 1-to-many relationship by default
    slots = db.relationship('Slot', backref='slot', lazy=True)
    notifications = db.relationship('Notification', backref='notification', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Slot(db.Model):
    __tablename__ = 'slot'
    id = db.Column(db.Integer, primary_key=True)
    starttime = db.Column(TIMESTAMP(timezone=True), default=datetime.now(timezone.utc)) 
    endtime = db.Column(TIMESTAMP(timezone=True), default=datetime.now(timezone.utc))
    # if user_id == null, then appt slot is open
    client = db.Column(db.Text, unique=False, default='None', nullable=True)
    provider = db.Column(db.Text, db.ForeignKey('user.email'), nullable=True)
    # slot will always have a provider
    # provider_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.String(512), unique=False, nullable=True)
    category = db.Column(db.String(50), unique=False, nullable=True) # atm,: Medical|Beauty|Fitness
    
    def __repr__(self):
	    return f'<Slot {self.description}>'

class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, unique=False, default='N/A', nullable=True)
    #seen = db.Column(db.Boolean, default=False)
    type = db.Column(db.Text, unique=False, default='N/A', nullable=True)
    sender = db.Column(db.Text, unique=False, default='None', nullable=True)
    recipient = db.Column(db.Text, db.ForeignKey('user.email'), nullable=True)

    def __repr__(self):
        return f'<Notification {self.message}>'
     

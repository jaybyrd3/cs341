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
    slots = db.relationship('Slot', backref='slot', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def notifications_count(self):
        return Notification.query.filter_by(user_id=self.id, read=False).count()

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
    description = db.Column(db.String(512), unique=False, nullable=True)
    category = db.Column(db.String(50), unique=False, nullable=True) # atm,: Medical|Beauty|Fitness
    
    def __repr__(self):
	    return f'<Slot {self.description}>'
    
class CancelledSlot(db.Model):
    __tablename__ = 'cancelledslot'
    id = db.Column(db.Integer, primary_key=True)
    starttime = db.Column(TIMESTAMP(timezone=True), default=datetime.now(timezone.utc)) 
    endtime = db.Column(TIMESTAMP(timezone=True), default=datetime.now(timezone.utc))
    # if user_id == null, then appt slot is open
    client = db.Column(db.Text, unique=False, default='None', nullable=True)
    provider = db.Column(db.Text, db.ForeignKey('user.email'), nullable=True)
    # slot will always have a provider
    description = db.Column(db.String(512), unique=False, nullable=True)
    category = db.Column(db.String(50), unique=False, nullable=True) # atm,: Medical|Beauty|Fitness
    
    def __repr__(self):
	    return f'<CancelledSlot {self.description}>'
    

class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    message = db.Column(db.String(256))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Notification {self.name}: {self.message}>'
    
def add_notification(user_id, name, message):
    notification = Notification(user_id=user_id, name=name, message=message)
    db.session.add(notification)
    db.session.commit()
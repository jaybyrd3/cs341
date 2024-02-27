# db_config.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Define your models here
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    #THE BELOW NEEDS TO CHANGE FOR FINAL IMPLEMENTATION
    password = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

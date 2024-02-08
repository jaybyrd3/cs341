from flask import Flask, request, render_template, redirect, url_for
from db_config import db, User
import os

app = Flask(__name__)

# Retrieve the database URL from the environment variables
database_url = os.getenv('DATABASE_URL')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the db with the app
db.init_app(app)

with app.app_context():
    db.create_all()

# Add your Flask routes here
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        if username and email:
            new_user = User(username=username, email=email)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('view_users'))
    return render_template('add_user.html')

@app.route('/users')
def view_users():
    users = User.query.all()
    return render_template('view_users.html', users=users)


if __name__ == '__main__':
    app.run(debug=True)

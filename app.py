from flask import Flask, request, render_template, redirect, url_for, flash
from db_config import db, User
from datetime import date, timedelta
from logging import FileHandler, WARNING
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
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

'''
@app.route('/signup', methods=['GET', 'POST'])
def signup():
	if request.method == 'POST':
		# Need to validate 2 things here:
		# The user doesn't currently exist
		# The user's passwords match
		email = request.form['email']
		password = request.form['password']
		confirm = request.form['confirm']
		if password == confirm and email and password and confirm:
			# query db to see if user exists
			user = User.query.filter_by(email = email).all()
			if not user:  # Check if user is an empty list
				# we know they're new & can add them
				new_user = User(email=email, username=email, password=password)
				db.session.add(new_user)
				db.session.commit()
				flash(f"You have successfully made an account under the email {email}!", category="success")
				return render_template('signup.html')
			else:
				# we know the user already exists
				flash(f"There is already an account registered under the email {email}. Please log in to continue.")
				return render_template('signup.html')
		else:
			flash(f"Your entered passwords do not match.", category="error")
			return render_template('signup.html')
	return render_template('signup.html')
'''
    

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

@app.route('/calendar')
def calendar():
    # Example for February 2024; adjust accordingly
    start_date = date(2024, 2, 1)
    end_date = date(2024, 2, 28)
    delta = timedelta(days=1)
    days = []
    
    while start_date <= end_date:
        days.append(start_date)
        start_date += delta

    return render_template('calendar.html', days=days)

# START Jinja test routes

@app.route('/base')
def base():
    return render_template('base.html')

@app.route('/childOfBase')
def childOfBase():
    return render_template('jinjaBootstrapTest.html')

@app.route('/index')
def index():
    return render_template('index.html')

# END Jinja test routes

if __name__ == '__main__':
    app.run(debug=True)

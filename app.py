from flask import Flask, request, session, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_required, login_user
from db_config import db, User, Slot
from datetime import date, timedelta
from logging import FileHandler, WARNING
from sqlalchemy import or_
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

# Initialize login manager
# NOTE: login manager documentation here: 
# https://flask-login.readthedocs.io/en/latest/
app.secret_key = 'SECRET_KEY'
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    return User.query.get(id)

#initialize secret key (we'll change this later)


# NOTE ON SESSIONS: The "session" object comes as a global-variable import
# with Flask & LoginManager. It automatically tracks who the current user is & their 
# information from one login to the next
# SESSIONS DOCUMENTATION:
# https://flask.palletsprojects.com/en/latest/quickstart/#sessions

with app.app_context():
    # comment this out to keep data
    # db.drop_all()
    db.create_all()

# Add your Flask routes here
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/skynet')
def wipe():
	db.drop_all()
	db.create_all()
	return "ITS ALL GONE!!!"

@app.route('/makeslot', methods=['GET', 'POST'])
@login_required
def makeslot():
	if request.method == 'POST':
		starttime = request.form['starttime']
		endtime = request.form['endtime']
		client = request.form['client']
		print(f"make slot client {client}")
		provider = request.form['provider']
		description = request.form['description']
		new_slot = Slot(starttime=starttime, endtime=endtime, client=client, provider=provider, description=description)
		db.session.add(new_slot)
		db.session.commit()
		return redirect(url_for('home')) 
	else:
		return render_template('makeslot.html')
      
@app.route('/booknew', methods=['GET', 'POST'])
@login_required
def booknew():
    if request.method == 'POST':
        slot_id = request.form.get('slot_id')
        slot = Slot.query.get(slot_id)
        if slot: #and not slot.client
            slot.client = session['email']  # Or however you identify the client
            db.session.commit()
            flash('Appointment booked successfully!', 'success')
            return redirect(url_for('viewappointments'))
        else:
            flash('This slot is no longer available.', 'error')
            return redirect(url_for('booknew'))
    
    open_slots = Slot.query.all() #filter_by(client=None).all()
    print(open_slots)
    return render_template('booknew.html', open_slots=open_slots)
# def booknew():
#     open_slots = Slot.query.filter_by(client=None).all()
#     if open_slots:
#           return render_template('booknew.html', open_slots=open_slots)
#     else:
#           return render_template('booknew.html', open_slots=None)
		

@app.route('/viewappointments', methods=['GET', 'POST'])
@login_required
def viewappointments():
    current_email = session.get('email')
    if current_email:
        pslots = Slot.query.filter_by(provider=current_email).all()
        cslots = Slot.query.filter_by(client=current_email).all()

        return render_template('viewappointments.html', pslots=pslots, cslots=cslots)
    else:
        return render_template('viewappointments.html', pslots=None, cslots=None)
         

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		# We need to see if they exist
		email = request.form['email']
		password = request.form['password']
		user = User.query.filter_by(email=email).filter_by(password=password).first()
		if not user:
			flash(f"Email/password is incorrect, or user does not exist.", category="error")
			return redirect(url_for('login'))
		else:
			session['email'] = email
			session['password'] = password
			login_user(user)
			flash(f"Congrats - you are now signed in as {email}!", category="success")
			# this may have to be '/' instead of 'index'
			return redirect(url_for('home'))
	else:
		return render_template('login.html')

# NOTE: I don't believe we need a "logout.html", as we're just 
# performing an action & flashing a message
#	>> i.e. will be page-independent & only accessed from header
@app.route('/logout')
@login_required
def logout():
	# remove username & password from session & redirect to index
	session.pop('email', None)
	session.pop('password', None)
	flash(f"You are now logged out.", category="success")
	return redirect(url_for('home'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
	if request.method == 'POST':
		# Need to validate 2 things here:
		# The user doesn't currently exist
		# The user's passwords match
		firstname = request.form['firstname']
		lastname = request.form['lastname']
		username = request.form['username']
		email = request.form['email']
		password = request.form['password']
		confirm = request.form['confirm']
		if password == confirm and email and password and confirm:
			# query db to see if user exists
			user = User.query.filter_by(email = email).first()
			if user:  # Check if user is an empty list
				# we know the user already exists
				flash(f"There is already an account registered under the email {email}. Please log in to continue.", category="error")
				return redirect(url_for('signup'))
			else:
                 # we know they're new & can add them
				new_user = User(email=email, username=username, password=password, firstName=firstname, lastName=lastname)
				db.session.add(new_user)
				db.session.commit()
				session['email'] = email
				session['password'] = password
				login_user(new_user)
				flash(f"You have successfully made an account under the email {email}!", category="success")
				return redirect(url_for('home')) 
		else:
			flash(f"Your entered passwords do not match.", category="error")
			return redirect(url_for('signup'))
	return render_template('signup.html')

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

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        firstName = request.form['firstname']
        lastName = request.form['lastname']
        jobTitle = request.form['jobtitle']
        qualifications = request.form['qualifications']

        # Validate that username and email are provided
        if username and email:
            # Check if the user already exists in the database
            existing_user = User.query.filter_by(username=username).first()

            if existing_user:
                # Update the fields for the existing user
                existing_user.email = email
                existing_user.firstName = firstName
                existing_user.lastName = lastName
                existing_user.jobTitle = jobTitle
                existing_user.qualifications = qualifications

                # Commit the changes to the database
                db.session.commit()
            else:
                # Handle the case where the user doesn't exist (optional)
                print("User not found in the database.")
            
            return redirect(url_for('home'))
    current_email = session.get('email')
    if current_email:  
        current_user = User.query.filter_by(email=current_email).first()
        first_name = current_user.firstName
        last_name = current_user.lastName
        user_name = current_user.username
        e_mail = current_email
        job_title = current_user.jobTitle
        qualifications_ = current_user.qualifications
        return render_template('account.html', first_name=first_name, last_name=last_name, user_name=user_name, e_mail=e_mail, job_title=job_title, qualifications_=qualifications_)
    else:
        return render_template('account.html', first_name="first name", last_name="last name", user_name="username", e_mail="email", job_title="job title", qualifications_="qualified?")

# [START] HELPER FUNCTIONS



# [END] HELPER FUNCTIONS


# run app
if __name__ == '__main__':
    app.run(debug=True)

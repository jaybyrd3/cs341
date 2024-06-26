from flask import Flask, request, session, render_template, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_required, login_user, logout_user
from db_config import db, User, Slot, Notification, CancelledSlot, add_notification
from datetime import date, timedelta, datetime, timezone
from logging import FileHandler, WARNING
from sqlalchemy import or_, and_, extract, func, select, types
from sqlalchemy.dialects.postgresql import TIMESTAMP
import os

#nID = 0

app = Flask(__name__)

# Retrieve the database URL from the environment variables
database_url = os.getenv('DATABASE_URL')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#DEBUG
app.config['SQLALCHEMY_ECHO'] = True

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
    user = User.query.filter_by(email=session.get('email')).first()
    if not user.jobTitle or not user.qualifications:
        flash(f"Sorry - you need to be registered as a provider to make a slot! Please enter in your job title & qualifications to continue.", category="error")
        return redirect(url_for('account'))
    elif request.method == 'POST':
        starttime = request.form['starttime']
        endtime = request.form['endtime']

        # Input Validation #
        # Convert the ISO 8601 date strings to datetime objects
        try:
            _starttime = datetime.fromisoformat(starttime)
            _endtime = datetime.fromisoformat(endtime)
        except ValueError:
            flash("Invalid date format.", category="error")
            return redirect(url_for('makeslot'))

        # Check if the start time is before the end time
        if _starttime >= _endtime:
            flash("Invalid slot window. Start must be chronologically before the end of slot.", category="error")
            return redirect(url_for('makeslot'))

        client = request.form['client']
        provider = request.form['provider']
        description = request.form['description']
        category = request.form['category']
        
        if starttime and endtime and client and provider and description and category:
            new_slot = Slot(starttime=starttime, endtime=endtime, client=client, provider=provider, description=description, category=category)
            db.session.add(new_slot)
            db.session.commit()
            return redirect(url_for('home'))
        else:
            flash(f"Please fill in all the required fields.", category="error")
            return redirect(url_for('makeslot'))
    else:
        return render_template('makeslot.html')
      

@app.route('/booknew', methods=['GET', 'POST'])
@login_required
def booknew():
    global nID
    if request.method == 'POST':
        slot_id = request.form.get('slot_id')
        slot = Slot.query.get(slot_id)
	# debug stuff
        # print(f"slot_id {slot_id} slot {slot}")
        if slot: #and not slot.client
            client_email = session.get('email')

            # Get start and end times of the selected slot
            selected_start_time = slot.starttime
            selected_end_time = slot.endtime

            # Check for conflicting slots
            conflicts = Slot.query.filter(
                (Slot.client == client_email) | (Slot.provider == client_email),
                Slot.starttime < selected_end_time,
                Slot.endtime > selected_start_time
            ).all()
            
            if conflicts:
                flash('You already have a booking that conflicts with this slot.', 'error')
                return redirect(url_for('booknew'))
            
            slot.client = client_email  # Or however you identify the client
	        #debug stuff
    	    # print(f"slot.client {session.get('email')}")
            # Notify provider
            #global nID
            #db.session.add(Notification(id=nID, sender=client_email, message=slot.client + " has scheduled an appointment with you during the " + slot.starttime.strftime('%I:%M %p') + " to " + slot.endtime.strftime('%I:%M %p') + " time slot on " + slot.starttime.strftime('%B %d, %Y') + "."))
            #nID += 1
            db.session.commit()
            flash('Appointment booked successfully!', 'success')
            provider = User.query.filter_by(email=slot.provider).first()
            client = User.query.filter_by(email=client_email).first()
            add_notification(provider.id, "Appointment Booked", "You have an appointment scheduled with " + client_email + " during the " + slot.starttime.strftime('%I:%M %p') + " to " + slot.endtime.strftime('%I:%M %p') + " time slot on " + slot.starttime.strftime('%B %d, %Y') + ".")
            add_notification(client.id, "Appointment Booked", "You have an appointment scheduled with " + slot.provider + " during the " + slot.starttime.strftime('%I:%M %p') + " to " + slot.endtime.strftime('%I:%M %p') + " time slot on " + slot.starttime.strftime('%B %d, %Y') + ".")
            return redirect(url_for('viewappointments'))
        else:
            flash('This slot is no longer available.', 'error')
            return redirect(url_for('booknew'))
    
    return render_template('booknew.html')


@app.route('/booknew/<category>', methods=['GET', 'POST'])
@login_required
def booknewcat(category):
    if request.method == 'GET':
         keyword = request.args.get('keyword', '')
         month = request.args.get('month', '')
         year = request.args.get('year', '')

         if keyword:
             keyword = keyword.lower()

        # Validate month
         if month:
             try:
                month_numeric = int(month)
                if not 1 <= month_numeric <= 12:
                    raise ValueError("Month must be between 1 and 12")
             except ValueError:
                return 'Invalid month', 400

        # Validate year
         if year:
             try:
                year_numeric = int(year)
                if not 2024 <= year_numeric <= 2026:
                    raise ValueError("Year must be between 2024 and 2026")
             except ValueError:
                return 'Invalid year', 400
        
         open_slots_query = Slot.query.filter(Slot.client == 'None') # SWS removed Slot.category == category
         # Maybe add here

         if keyword:
            open_slots_query = open_slots_query.filter(Slot.description.ilike(f'%{keyword}%'))

         if month:
            open_slots_query = open_slots_query.filter(
                or_(
                    extract('month', Slot.starttime) == month_numeric,
                    extract('month', Slot.endtime) == month_numeric
                )
            )

         if year:
            open_slots_query = open_slots_query.filter(
                or_(
                    extract('year', Slot.starttime) == year_numeric,
                    extract('year', Slot.endtime) == year_numeric
                )
            )

         if category == 'all':
              open_slots = open_slots_query.all()

              now = datetime.now(timezone.utc)
                      # Process cancellation for past slots
              for slot in list(open_slots):  # Use list to duplicate items to modify during iteration
                  if slot.starttime < now:
                    # Add to cancelled slots
                    cancelled_slot = CancelledSlot(
                        starttime=slot.starttime,
                        endtime=slot.endtime,
                        client=slot.client,
                        provider=slot.provider,
                        description=slot.description,
                        category=slot.category
                    )
                    db.session.add(cancelled_slot)
                    db.session.delete(slot)

              db.session.commit()
         else:
              open_slots = open_slots_query.filter_by(category=category).all()
         return render_template('booknew.html', open_slots=open_slots, cansearch=True)
    else:
          return "You sent a POST request to " + str(category) + ". Why, though?"


@app.route('/cancel_appointment', methods=['POST'])
@login_required
def cancel_appointment():
    #global nID
    slot_id = request.form.get('slot_id')
    slot = Slot.query.get(slot_id)
    current_email = session.get('email')
    if slot:
        client = User.query.filter_by(email=slot.client).first()
        provider = User.query.filter_by(email=slot.provider).first()
        user = User.query.filter_by(email=current_email).first()
        if user and (slot.client == current_email or slot.provider == current_email or user.is_admin):

            # Create a new cancelled slot with data from the original slot
            cancelled_slot = CancelledSlot(
                starttime=slot.starttime,
                endtime=slot.endtime,
                client=slot.client,
                provider=slot.provider,
                description=slot.description,
                category=slot.category
            )
            db.session.add(cancelled_slot)  # Add the cancelled slot to the database

            # Update the slot to indicate cancellation
            if user.is_admin:
                flash('Appointment DESTROYED successfully', 'success')
                add_notification(client.id, "Appointment Cancelled", "Your appointment with " + provider.firstName + " at " + slot.starttime.strftime('%B %d, %I:%M %p, %Y') + " has been cancelled by an Admin.")
                add_notification(provider.id, "Appointment Cancelled", "Your appointment with " + client.firstName + " at " + slot.starttime.strftime('%B %d, %I:%M %p, %Y') + " has been cancelled by an Admin.")
                db.session.delete(slot)
                db.session.commit()
            elif slot.provider == current_email:
                # If provider, delete from db & notify client
                #db.session.add(Notification(id=nID, sender=current_email, recipient=slot.client, message="Your appointment with " + slot.provider + " at " + slot.starttime.strftime('%B %d, %I:%M %p, %Y') + " has been cancelled."))
                #nID += 1

                flash('Appointment DESTROYED successfully', 'success')
                if client:
                    add_notification(client.id, "Appointment Cancelled", "Your appointment with " + provider.firstName + " at " + slot.starttime.strftime('%B %d, %I:%M %p, %Y') + " has been cancelled.")
                db.session.delete(slot)
                db.session.commit()
            else:
                slot.client = "None"  # or another appropriate action
                # Notify provider
                #db.session.add(Notification(id=nID, sender=current_email, recipient=slot.client, message="Your appointment with " + slot.client + " at " + slot.starttime.strftime('%B %d, %I:%M %p, %Y') + " has been cancelled."))
                #nID += 1
                flash('Appointment canceled successfully.', 'success')
                provider = User.query.filter_by(email=slot.provider).first()
                add_notification(provider.id, "Appointment Cancelled", "Your appointment with " + client.firstName + " at " + slot.starttime.strftime('%B %d, %I:%M %p, %Y') + " has been cancelled.")
                db.session.commit()
        else:
            flash('You do not have permission to cancel this appointment', 'error')
    else:
        flash('Appointment could not be found', 'error')

    return redirect(url_for('viewappointments'))


@app.route('/viewappointments', methods=['GET', 'POST'])
@login_required
def viewappointments():
    current_email = session.get('email')

    if request.method == 'GET' and current_email:
         keyword = request.args.get('keyword', '')
         month = request.args.get('month', '')
         year = request.args.get('year', '')

         if keyword:
             keyword = keyword.lower()

        # Validate month
         if month:
             try:
                month_numeric = int(month)
                if not 1 <= month_numeric <= 12:
                    raise ValueError("Month must be between 1 and 12")
             except ValueError:
                return 'Invalid month', 400

        # Validate year
         if year:
             try:
                year_numeric = int(year)
                if not 2024 <= year_numeric <= 2026:
                    raise ValueError("Year must be between 2024 and 2026")
             except ValueError:
                return 'Invalid year', 400
         
         isAdmin = False
         user = User.query.filter_by(email=session.get('email')).first()
         if user.is_admin:
             pslots = Slot.query # Booked Slots
             cslots = Slot.query.filter(Slot.client == 'None') # Available Slots
             isAdmin = True
         else:
            pslots = Slot.query.filter(Slot.provider == current_email) #.filter_by(provider=current_email).all()
            cslots = Slot.query.filter(Slot.client == current_email)

         if keyword:
             if cslots:
                 cslots = cslots.filter(Slot.description.ilike(f'%{keyword}%'))
             if pslots:
                 pslots = pslots.filter(Slot.description.ilike(f'%{keyword}%'))

         if month:
              if cslots:
                cslots = cslots.filter(
                    or_(
                        extract('month', Slot.starttime) == month_numeric,
                        extract('month', Slot.endtime) == month_numeric
                    )
                )
              if pslots:
                pslots = pslots.filter(
                    or_(
                        extract('month', Slot.starttime) == month_numeric,
                        extract('month', Slot.endtime) == month_numeric
                    )
                )

         if year:
              if cslots:
                cslots = cslots.filter(
                    or_(
                        extract('year', Slot.starttime) == year_numeric,
                        extract('year', Slot.endtime) == year_numeric
                    )
                )
              if pslots:
                pslots = pslots.filter(
                    or_(
                        extract('year', Slot.starttime) == year_numeric,
                        extract('year', Slot.endtime) == year_numeric
                    )
                )
         if cslots:
            cslots = cslots.all()
         if pslots:
            pslots = pslots.all()
            
         if user.is_admin:
             cancelled = CancelledSlot.query.all()
         else:
             cancelled = CancelledSlot.query.filter((CancelledSlot.client == current_email) | (CancelledSlot.provider == current_email))
             if cancelled:
                 cancelled = cancelled.all()
         
         return render_template('viewappointments.html', pslots=pslots, cslots=cslots, isAdmin=isAdmin, cancelled=cancelled)
    else:
         return render_template('viewappointments.html', pslots=None, cslots=None, isAdmin=isAdmin)


@app.route('/viewappointments/<account_email>')
@login_required
def viewappointments_admin(account_email):
    current_email = session.get('email')
    current_user = User.query.filter_by(email=current_email).first()
    if current_user and current_user.is_admin:
        requested_user = User.query.filter_by(email=account_email).first()
        if not requested_user or not requested_user.is_active:
            flash(f"Sorry - requested user not found!", category="error")
            return redirect(url_for('home'))
        else:
            pslots = Slot.query.filter(Slot.provider == account_email) #.filter_by(provider=current_email).all()
            cslots = Slot.query.filter(Slot.client == account_email)
            cancelled = CancelledSlot.query.filter((CancelledSlot.client == account_email) | (CancelledSlot.provider == account_email))
            if pslots:
                pslots = pslots.all()
            if cslots:
                cslots = cslots.all()
            if cancelled:
                cancelled = cancelled.all()
            return render_template('viewappointments.html', pslots=pslots, cslots=cslots, e_mail=account_email, cancelled=cancelled)
    else:
        if not current_user:
            flash(f"Sorry - you need to be logged in as an admin to access that page!", category="error")
            return redirect(url_for('home'))
        else:
            flash(f"Sorry - you need to be an admin to access that page!", category="error")
            return redirect(url_for('home'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get("email") is not None:
        flash(f"You are already logged in.", category="error")
        return redirect(url_for('home'))
    else:
        if request.method == 'POST':
            # We need to see if they exist
            email = request.form['email']
            password = request.form['password']
            # changed to support hashing
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password) and user.is_active:
                session['email'] = email
                session['password'] = password
                login_user(user)
                flash(f"Congrats - you are now signed in as {email}!", category="success")
                # this may have to be '/' instead of 'index'
                return redirect(url_for('home'))
            else:
                
                flash(f"Email/password is incorrect, or user does not exist.", category="error")
                return redirect(url_for('login'))
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
	logout_user() # logs out user & cleans up cookies
	flash(f"You are now logged out.", category="success")
	return redirect(url_for('home'))


@app.route('/delete')
@login_required
def delete():
    #global nID
    user = User.query.filter_by(email=session.get('email')).first()
    user.is_active = False
    db.session.commit()
    # now we need to notify all relevant parties
    pslots = Slot.query.filter(Slot.provider == user.email) #.filter_by(provider=current_email).all()
    cslots = Slot.query.filter(Slot.client == user.email)
    if pslots:
        for slot in pslots:
            if slot.client:
                #notif = Notification(id=nID, sender=user.email, recipient=slot.client, message="Your appointment with " + slot.provider + " at " + slot.starttime.strftime('%B %d, %I:%M %p, %Y') + " has been cancelled.")
                #nID += 1
                #db.session.add(notif)
                # Create a new cancelled slot with data from the original slot
                cancelled_slot = CancelledSlot(
                    starttime=slot.starttime,
                    endtime=slot.endtime,
                    client=slot.client,
                    provider=slot.provider,
                    description=slot.description,
                    category=slot.category
                )
                db.session.add(cancelled_slot)  # Add the cancelled slot to the database

                add_notification(slot.client.id, "Appointment Cancelled", "Your appointment with " + slot.provider.firstName + " at " + slot.starttime.strftime('%B %d, %I:%M %p, %Y') + " has been cancelled.")
                db.session.delete(slot)
                db.session.commit()
    if cslots:
        for slot in cslots:
            #notif = Notification(id=nID, sender=user.email, recipient=slot.client, message="Your appointment with " + slot.client + " at " + slot.starttime.strftime('%B %d, %I:%M %p, %Y') + " has been cancelled.")
            #nID += 1
            #db.session.add(notif)
            # Create a new cancelled slot with data from the original slot
            cancelled_slot = CancelledSlot(
                starttime=slot.starttime,
                endtime=slot.endtime,
                client=slot.client,
                provider=slot.provider,
                description=slot.description,
                category=slot.category
            )
            db.session.add(cancelled_slot)  # Add the cancelled slot to the database

            add_notification(slot.provider.id, "Appointment Cancelled", "Your appointment with " + slot.client.firstName + " at " + slot.starttime.strftime('%B %d, %I:%M %p, %Y') + " has been cancelled.")
            db.session.delete(slot)
            db.session.commit()
    flash(f"You have successfully deleted your account.", category="success")
    return redirect(url_for('home'))


@app.route('/delete/<account_email>')
@login_required
def admin_delete(account_email):
    #global nID
    current_email = session.get('email')
    current_user = User.query.filter_by(email=current_email).first()
    if current_user and current_user.is_admin:
        requested_user = User.query.filter_by(email=account_email).first()
        if not requested_user or not requested_user.is_active:
            flash(f"Sorry - requested user not found!", category="error")
            return redirect(url_for('home'))
        else:
            requested_user.is_active = False
            db.session.commit()
            # now we need to notify all relevant parties
            pslots = Slot.query.filter(Slot.provider == requested_user.email) #.filter_by(provider=current_email).all()
            cslots = Slot.query.filter(Slot.client == requested_user.email)
            if pslots:
                for slot in pslots:
                    if slot.client:
                        #notif = Notification(id=nID, sender=requested_user.email, recipient=slot.client, message="Your appointment with " + slot.provider + " at " + slot.starttime.strftime('%B %d, %I:%M %p, %Y') + " has been cancelled.")
                        #nID += 1
                       # db.session.add(notif)
                                    # Create a new cancelled slot with data from the original slot
                        cancelled_slot = CancelledSlot(
                            starttime=slot.starttime,
                            endtime=slot.endtime,
                            client=slot.client,
                            provider=slot.provider,
                            description=slot.description,
                            category=slot.category
                        )
                        db.session.add(cancelled_slot)  # Add the cancelled slot to the database
                        add_notification(slot.client.id, "Appointment Cancelled", "Your appointment with " + slot.provider.firstName + " at " + slot.starttime.strftime('%B %d, %I:%M %p, %Y') + " has been cancelled by an Admin.")
                        db.session.delete(slot)
                        db.session.commit()
            if cslots:
                for slot in cslots:
                    #notif = Notification(id=nID, sender=requested_user.email, recipient=slot.client, message="Your appointment with " + slot.client + " at " + slot.starttime.strftime('%B %d, %I:%M %p, %Y') + " has been cancelled.")
                    #nID += 1
                    #db.session.add(notif)
                    # Create a new cancelled slot with data from the original slot
                    cancelled_slot = CancelledSlot(
                        starttime=slot.starttime,
                        endtime=slot.endtime,
                        client=slot.client,
                        provider=slot.provider,
                        description=slot.description,
                        category=slot.category
                    )
                    db.session.add(cancelled_slot)  # Add the cancelled slot to the database
                    add_notification(slot.provider.id, "Appointment Cancelled", "Your appointment with " + slot.client.firstName + " at " + slot.starttime.strftime('%B %d, %I:%M %p, %Y') + " has been cancelled by an Admin.")
                    db.session.delete(slot)
                    db.session.commit()
            flash(f"You have successfully deleted " + requested_user.email + "'s account.", category="success")
            return redirect(url_for('home'))
    else:
        if not current_user:
            flash(f"Sorry - you need to be logged in as an admin to access that page!", category="error")
            return redirect(url_for('home'))
        else:
            flash(f"Sorry - you need to be an admin to access that page!", category="error")
            return redirect(url_for('home'))


@app.route('/reactivate')
@login_required
def reactivate_unspecified():
    current_email = session.get('email')
    current_user = User.query.filter_by(email=current_email).first()
    if current_user and current_user.is_admin:
        flash(f"Sorry - you need to specify an account to reactivate within the URL via the following convention: /reactivate/<account_email> (or click the link labeled Reactivate next to the desired account)", category="error")
        return redirect(url_for('view_users'))
    else:
        if not current_user:
            flash(f"Sorry - you need to be logged in as an admin to access that page!", category="error")
            return redirect(url_for('home'))
        else:
            flash(f"Sorry - you need to be an admin to access that page!", category="error")
            return redirect(url_for('home'))


@app.route('/reactivate/<account_email>')
@login_required
def reactivate(account_email):
    current_email = session.get('email')
    current_user = User.query.filter_by(email=current_email).first()
    if current_user and current_user.is_admin:
        requested_user = User.query.filter_by(email=account_email).first()
        if not requested_user:
            flash(f"Sorry - requested user not found!", category="error")
            return redirect(url_for('home'))
        elif requested_user.is_active:
            flash(f"Specified account is already marked as active.", category="error")
            return redirect(url_for('home'))
        else:
            requested_user.is_active = True
            db.session.commit()
            flash(f"You have successfully reactivated " + requested_user.email + "'s account.", category="success")
            add_notification(requested_user.id, "Account Reactivated", "Your account has been reactivated by an Admin.")
            return redirect(url_for('home'))
    else:
        if not current_user:
            flash(f"Sorry - you need to be logged in as an admin to access that page!", category="error")
            return redirect(url_for('home'))
        else:
            flash(f"Sorry - you need to be an admin to access that page!", category="error")
            return redirect(url_for('home'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if session.get("email") is not None:
        flash(f"You are already logged in.", category="error")
        return redirect(url_for('home'))
    else:
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
                    new_user = User(email=email, username=username, firstName=firstname, lastName=lastname)
                    # hash password with built in hash function
                    new_user.set_password(password)
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
@login_required
def add_user():
    user = User.query.filter_by(email=session.get('email')).first()
    if not user.is_admin:
        flash(f"Sorry - you need to be an admin to access that page!", category="error")
        return redirect(url_for('home'))
    else:
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
@login_required
def view_users():
    user = User.query.filter_by(email=session.get('email')).first()
    if not user.is_admin:
        flash(f"Sorry - you need to be an admin to access that page!", category="error")
        return redirect(url_for('home'))
    else:
        users = User.query.all()
        return render_template('view_users.html', users=users)


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
        #notifications_ = Notification.query.filter_by(recipient=current_email).all()
        return render_template('account.html', first_name=first_name, last_name=last_name, user_name=user_name, e_mail=e_mail, job_title=job_title, qualifications_=qualifications_)#, notifications_=notifications_)
    else:
        return render_template('account.html', first_name="first name", last_name="last name", user_name="username", e_mail="email", job_title="job title", qualifications_="qualified?")#, notifications_=[]) # using "[]" here may make this break


@app.route('/account/<account_email>')
@login_required
def admin_view(account_email):
    current_email = session.get('email')
    current_user = User.query.filter_by(email=current_email).first()
    if current_user and current_user.is_admin:
        requested_user = User.query.filter_by(email=account_email).first()
        if not requested_user or not requested_user.is_active:
            flash(f"Sorry - requested user not found!", category="error")
            return redirect(url_for('home'))
        else:
            first_name = requested_user.firstName
            last_name = requested_user.lastName
            user_name = requested_user.username
            e_mail = account_email
            job_title = requested_user.jobTitle
            qualifications_ = requested_user.qualifications
            #notifications_ = Notification.query.filter_by(recipient=e_mail).all()
            return render_template('account.html', first_name=first_name, last_name=last_name, user_name=user_name, e_mail=e_mail, job_title=job_title, qualifications_=qualifications_)#, notifications_=notifications_)
    else:
        if not current_user:
            flash(f"Sorry - you need to be logged in as an admin to access that page!", category="error")
            return redirect(url_for('home'))
        else:
            flash(f"Sorry - you need to be an admin to access that page!", category="error")
            return redirect(url_for('home'))
'''
@app.route('/account/dismiss/<nID>')
@login_required
def dismiss(nID):
    current_email = session.get('email')
    current_user = User.query.filter_by(email=current_email).first()
    if current_user:
        notification = Notification.query.filter_by(id=nID).first()
        if notification:
            db.session.delete(notification)
            db.session.commit()
        return redirect(url_for('account'))
    else:
        flash(f"Sorry - you need to be logged in to access that page!", category="error")
        return redirect(url_for('home'))
'''
# loads in demo 1 data after a db change
@app.route('/demo1', methods=['GET'])
def demo1():
    abc = User.query.filter_by(email="abc@xyz.com").first()
    admin = User.query.filter_by(email="admin@test.com").first()
    abby = User.query.filter_by(email="abbyandersen@test.com").first()
    katie = User.query.filter_by(email="katiejohnson@test.com").first()
    jane = User.query.filter_by(email="janedoe@test.com").first()
    users_with_qualifications = []
    if not abc:
        users_with_qualifications.append
        (
            User (
                username = "abc",
                email = "abc@xyz.com",
                is_admin = True
            )
        )
    if not admin:
        print("----->DEBUG: Admin not found; adding to list")
        users_with_qualifications.append
        (
            User (
                username = "admin",
                email = "admin@test.com",
                is_admin = True
            )
        )
    if not abby:
        print("----->DEBUG: Abby not found; adding to list")
        users_with_qualifications.append
        (
            User (
                firstName = "Abby",
                lastName = "Andersen",
                email = "abbyandersen@test.com",
                qualifications = "Graduated from The Salon Professional Academy, 2015",
                jobTitle = "Hair Specialist"
            )
        )
    if not katie:
        print("----->DEBUG: Katie not found; adding to list")
        users_with_qualifications.append
        (
            User (
                firstName = "Katie",
                lastName = "Johnson",
                email = "katiejohnson@test.com",
                qualifications = "Skin-care certified nurse training, 2021",
                jobTitle = "Skin Care Nurse"
            )
        )
    if not jane:
        print("----->DEBUG: Jane not found; adding to list")
        users_with_qualifications.append
        (
            User (
                firstName = "Jane",
                lastName = "Doe",
                email = "janedoe@test.com"
            )
        )
    abbyslot = Slot.query.filter_by(provider="abbyandersen@test.com").first()
    katieslot = Slot.query.filter_by(provider="katiejohnson@test.com").first()
    slots_details = []
    if not abbyslot:
        print("----->DEBUG: AbbySlot not found; adding to list")
        slots_details.append
        (
            Slot (
                provider = "abbyandersen@test.com",
                client = "janedoe@test.com",
                description = "Hair Highlights",
                category = "beauty",
                starttime = "2024-03-04 15:00:00 UTC",
                endtime = "2024-03-04 16:00:00 UTC"
            )
        )
    if not katieslot:
        print("----->DEBUG: KatieSlot not found; adding to list")
        slots_details.append
        (
            Slot (
                provider = "katiejohnson@test.com",
                client = None,
                description = "Face Moisture Treatment",
                category = "beauty",
                starttime = "2024-03-04 15:00:00 UTC",
                endtime = "2024-03-04 16:00:00 UTC"
            )
        )
        
    # Insert users into the database
    for user in users_with_qualifications:
        user.set_password("123")  # Set a default password
        db.session.add(user)
        print("----->DEBUG: Added ", user.email)
    db.session.commit()
    # Insert slots into the database
    for slot in slots_details: 
        db.session.add(slot)
    db.session.commit()

    flash(f"Demo 1 data preloaded successfully!", category="success")
    return redirect(url_for('home'))
    #return jsonify({"message": "Demo 1 data preloaded successfully!"})

#notification functions
@app.route('/notifications/count')
@login_required
def notifications_count():
    current_email = session.get('email')
    current_user = User.query.filter_by(email=current_email).first()
    count = Notification.query.filter_by(user_id=current_user.id, read=False).count()
    return jsonify(count=count)


@app.route('/notifications')
@login_required
def notifications():
    current_email = session.get('email')
    current_user = User.query.filter_by(email=current_email).first()
    unread_notifications = Notification.query.filter_by(user_id=current_user.id, read=False).all()
    return render_template('notifications.html', notifications=unread_notifications)


@app.route('/dismiss_notification/<int:notification_id>', methods=['POST'])
@login_required
def dismiss_notification(notification_id):
    current_email = session.get('email')
    current_user = User.query.filter_by(email=current_email).first()
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        flash('You do not have permission to do that.', 'danger')
        return redirect(url_for('notifications'))
    
    notification.read = True
    db.session.commit()
    flash('Notification dismissed.', 'success')
    if notifications_count != 0:
        return redirect(url_for('notifications'))
    else:
        return redirect(url_for('home'))

#report functions
@app.route('/report')
@login_required
def generate_report(users=None, start_date=None, end_date=None):
    month = request.args.get('month', '')
    year = request.args.get('year', '')

    slots_query = Slot.query
    cancelled_query = CancelledSlot.query

    if month:
        try:
            month_numeric = int(month)
            if not 1 <= month_numeric <= 12:
                raise ValueError("Month must be between 1 and 12")
            else:
                slots_query = slots_query.filter(
                    or_(
                        extract('month', Slot.starttime) == month_numeric,
                        extract('month', Slot.endtime) == month_numeric
                    )
                )
                cancelled_query = cancelled_query.filter(
                    or_(
                        extract('month', Slot.starttime) == month_numeric,
                        extract('month', Slot.endtime) == month_numeric
                    )
                )
        except ValueError:
            return 'Invalid month', 400
        
    if year:
        try:
            year_numeric = int(year)
            if not 2024 <= year_numeric <= 2026:
                raise ValueError("Year must be between 2024 and 2026")
            else:
                slots_query = slots_query.filter(
                    or_(
                        extract('year', Slot.starttime) == year_numeric,
                        extract('year', Slot.endtime) == year_numeric
                    )
                )
                cancelled_query = cancelled_query.filter(
                    or_(
                        extract('year', Slot.starttime) == year_numeric,
                        extract('year', Slot.endtime) == year_numeric
                    )
                )
        except ValueError:
            return 'Invalid year', 400
        

    slots = slots_query.all()
    cancelled = cancelled_query.all()
    number_of_slots = len(slots)
    number_of_cancelled = len(cancelled)
    number_of_clients = len(set([slot.client for slot in slots]))
    number_of_providers = len(set([slot.provider for slot in slots]))
    number_of_categories = len(set([slot.category for slot in slots]))
    report_data = {
        "number_of_slots": number_of_slots,
        "number_of_cancelled": number_of_cancelled,
        "number_of_clients": number_of_clients,
        "number_of_providers": number_of_providers,
        "number_of_categories": number_of_categories
    }
    provider_hours = {}
    for slot in slots:
        if slot.provider not in provider_hours:
            provider_hours[slot.provider] = 0
        provider_hours[slot.provider] += (slot.endtime - slot.starttime).seconds / 3600
    report_data["provider_hours"] = provider_hours
    return render_template('report.html', report_data=report_data)


# run app
if __name__ == '__main__':
    app.run(debug=True)

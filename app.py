from flask import Flask, render_template,render_template_string, request
from flask_sqlalchemy import SQLAlchemy
import os
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

# Create the database tables
def create_database():
    with app.app_context():
        db.create_all()

# Define a route for the default page
@app.route('/')
def index():
    return render_template_string("""
        <form method="POST" action="/submit">
            Username: <input type="text" name="username"><br>
            Email: <input type="email" name="email"><br>
            <input type="submit">
        </form>
    """)

# Define a route to handle form submissions
@app.route('/submit', methods=['POST'])
def submit():
    username = request.form['username']
    email = request.form['email']

    # Input validation can be added here
    if not username or not email:
        return "Invalid input.", 400

    # Check if the user already exists
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return "Username or email already exists.", 400

    # Create a new user and add it to the database
    new_user = User(username=username, email=email)
    db.session.add(new_user)
    db.session.commit()

    return "User added successfully."

# @app.route('/')
# def home():
#     return render_template('home.html')

# @app.route('/jay')
# def jay():
#     return render_template('jay.html')

# @app.route('/test')
# def test():
#     return render_template('jay.html')

# @app.route('/form', methods=['GET', 'POST'])
# def index():
#     if request.method == 'POST':
#         user_input = request.form['user_input']
#         return render_template('result.html', user_input=user_input)
#     return render_template('index.html')

if __name__ == '__main__':
    create_database()
    app.run(debug=True)

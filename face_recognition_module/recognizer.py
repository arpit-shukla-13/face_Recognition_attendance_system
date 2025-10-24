from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash # For password hashing
import secrets # For session key

# 1. --- App and Database Configuration ---

app = Flask(__name__)

# Secret key is needed for session management
app.config['SECRET_KEY'] = secrets.token_hex(16)

# Set the path for the database file
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set paths for file uploads
UPLOAD_FOLDER_ABS = os.path.join(app.root_path, 'static', 'uploads', 'employee_photos')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER_ABS
UPLOAD_FOLDER_REL = os.path.join('uploads', 'employee_photos')

# Initialize the database
db = SQLAlchemy(app)

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER_ABS):
    os.makedirs(UPLOAD_FOLDER_ABS)


# 2. --- Database Models (Tables) ---

class Employee(db.Model):
    # ... (Employee model jaisa tha waisa hi hai, koi change nahi)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    photo_path = db.Column(db.String(200), nullable=False)
    attendances = db.relationship('Attendance', backref='employee', lazy=True)

    def __repr__(self):
        return f'<Employee {self.name}>'

class Attendance(db.Model):
    # ... (Attendance model jaisa tha waisa hi hai, koi change nahi)
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)

    def __repr__(self):
        return f'<Attendance {self.employee.name} on {self.date}>'

# --- NEW ADMIN TABLE ---
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<Admin {self.username}>'


# 3. --- Routes (Our Web Pages) ---

# --- NEW ADMIN ROUTES ---

@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if admin already exists
        existing_admin = Admin.query.filter_by(username=username).first()
        if existing_admin:
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('admin_signup'))
            
        # Hash the password for security
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        new_admin = Admin(username=username, password_hash=hashed_password)
        db.session.add(new_admin)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('admin_login'))
        
    return render_template('admin_signup.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = Admin.query.filter_by(username=username).first()
        
        # Check if admin exists and password is correct
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            flash('Logged in successfully!', 'success')
            # TODO: Redirect to the new admin dashboard
            return f"Welcome {admin.username}! Dashboard is under construction."
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('admin_login'))
            
    return render_template('admin_login.html')


# TODO: We will create the routes for the User Module later
@app.route('/')
def user_dashboard():
    return "User Dashboard - Under Construction"

# ... (Purane employee routes abhi ke liye yahan se hata diye gaye hain)
# ... (Hum unhe secure karke admin dashboard mein add karenge)


# Main entry point to run the app
if __name__ == "__main__":
    with app.app_context():
        db.create_all() # This will create the new 'admin' table
    app.run(debug=True)
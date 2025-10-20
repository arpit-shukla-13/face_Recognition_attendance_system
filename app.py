from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import date # We need this to store the date

# 1. --- App and Database Configuration ---

app = Flask(__name__)

# Set the path for the database file
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Disable a warning

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
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True) # Added unique=True
    photo_path = db.Column(db.String(200), nullable=False)
    # This creates a relationship: "Get all attendance records for this employee"
    attendances = db.relationship('Attendance', backref='employee', lazy=True)

    def __repr__(self):
        return f'<Employee {self.name}>'

# --- NEW TABLE ---
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today) # Stores the date
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False) # Link to Employee table

    def __repr__(self):
        return f'<Attendance {self.employee.name} on {self.date}>'


# 3. --- Routes (Our Web Pages) ---

@app.route('/')
def index():
    employees = Employee.query.all()
    # TODO: In the next step, we will also fetch and show attendance data
    return render_template('index.html', employees=employees)


@app.route('/add')
def add_employee_page():
    return render_template('add_employee.html')


@app.route('/add_employee', methods=['POST'])
def add_employee_data():
    if request.method == 'POST':
        employee_name = request.form['name']
        photo = request.files['photo']
        
        # Check if employee already exists
        existing_employee = Employee.query.filter_by(name=employee_name).first()
        if existing_employee:
            print(f"Employee name {employee_name} already exists.")
            # We should probably show an error to the user, but for now we redirect
            return redirect(url_for('index'))

        if photo:
            filename = secure_filename(photo.filename)
            unique_filename = str(uuid.uuid4()) + "_" + filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            db_path = os.path.join(UPLOAD_FOLDER_REL, unique_filename).replace("\\", "/")
            
            photo.save(save_path)
            
            new_employee = Employee(
                name=employee_name,
                photo_path=db_path 
            )
            
            try:
                db.session.add(new_employee)
                db.session.commit()
                print(f"Employee {employee_name} added with photo path: {db_path}")
            except Exception as e:
                print(f"Error adding to database: {e}")
                db.session.rollback()
                
        return redirect(url_for('index'))


# Main entry point to run the app
if __name__ == "__main__":
    # This will create both 'employee' and 'attendance' tables if they don't exist
    with app.app_context():
        db.create_all()
    app.run(debug=True)
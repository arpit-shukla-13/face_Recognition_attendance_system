from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from functools import wraps # We need this to create the 'Guard'

# 1. --- App and Database Configuration ---






app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER_ABS = os.path.join(app.root_path, 'static', 'uploads', 'employee_photos')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER_ABS
UPLOAD_FOLDER_REL = os.path.join('uploads', 'employee_photos')
db = SQLAlchemy(app)

if not os.path.exists(UPLOAD_FOLDER_ABS):
    os.makedirs(UPLOAD_FOLDER_ABS)


# 2. --- Database Models (Tables) ---
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    photo_path = db.Column(db.String(200), nullable=False)
    attendances = db.relationship('Attendance', backref='employee', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)


# 3. --- Login Guard (Decorator) ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# 4. --- Admin Login/Signup/Logout Routes ---

@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_admin = Admin.query.filter_by(username=username).first()
        if existing_admin:
            flash('Username already exists.', 'error')
            return redirect(url_for('admin_signup'))
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
        
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('admin_login'))
    return render_template('admin_login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('admin_login'))


# 5. --- Admin Dashboard (Employee Management) ---

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    try:
        today = date.today()
        employees = Employee.query.all()
        todays_attendance = Attendance.query.filter_by(date=today).all()
        present_employee_names = [record.employee.name for record in todays_attendance]
        
        return render_template('admin_dashboard.html', 
                               employees=employees, 
                               attendance=todays_attendance, 
                               present_names=present_employee_names,
                               today=today)
    except Exception as e:
        print(f"Error in admin_dashboard route: {e}")
        return "An error occurred."

@app.route('/admin/add', methods=['GET'])
@login_required
def admin_add_employee_page():
    return render_template('add_employee.html')


@app.route('/admin/add_employee', methods=['POST'])
@login_required
def admin_add_employee_data():
    if request.method == 'POST':
        employee_name = request.form['name']
        photo = request.files['photo']
        
        existing_employee = Employee.query.filter_by(name=employee_name).first()
        if existing_employee:
            flash(f"Employee name {employee_name} already exists.", 'error')
            return redirect(url_for('admin_dashboard'))

        if photo:
            filename = secure_filename(photo.filename)
            unique_filename = str(uuid.uuid4()) + "_" + filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            db_path = os.path.join(UPLOAD_FOLDER_REL, unique_filename).replace("\\", "/")
            photo.save(save_path)
            new_employee = Employee(name=employee_name, photo_path=db_path)
            
            try:
                db.session.add(new_employee)
                db.session.commit()
                flash(f"Employee {employee_name} added successfully.", 'success')
                print(f"Employee {employee_name} added.")
                
                print("Running trainer in background...")
                trainer_script_path = os.path.join('face_recognition_module', 'trainer.py')
                os.system(f'python {trainer_script_path}')
                print("Training complete.")

            except Exception as e:
                print(f"Error adding to database: {e}")
                db.session.rollback()
                
        return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete/<int:employee_id>')
@login_required
def admin_delete_employee(employee_id):
    try:
        employee = Employee.query.get(employee_id)
        if not employee:
            flash('Employee not found.', 'error')
            return redirect(url_for('admin_dashboard'))

        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(employee.photo_path))

        Attendance.query.filter_by(employee_id=employee.id).delete()
        
        db.session.delete(employee)
        db.session.commit()

        if os.path.exists(photo_path):
            os.remove(photo_path)
            print(f"Deleted photo: {photo_path}")
        else:
            print(f"Warning: Photo not found, could not delete: {photo_path}")

        print("Running trainer in background after deletion...")
        trainer_script_path = os.path.join('face_recognition_module', 'trainer.py')
        os.system(f'python {trainer_script_path}')
        print("Training complete.")

        flash(f'Employee {employee.name} and all associated data deleted successfully.', 'success')

    except Exception as e:
        db.session.rollback()
        print(f"Error deleting employee: {e}")
        flash('Error deleting employee. Please check logs.', 'error')

    return redirect(url_for('admin_dashboard'))


# --- NEW EDIT EMPLOYEE ROUTES (GET and POST) ---
@app.route('/admin/edit/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_employee(employee_id):
    # 1. Find the employee by ID, or return 404 if not found
    employee = Employee.query.get_or_404(employee_id)
    
    # 2. If it's a POST request (form submitted)
    if request.method == 'POST':
        try:
            new_name = request.form['name']
            photo = request.files['photo']
            
            # Check if name is being changed and if new name already exists
            if new_name != employee.name:
                existing_employee = Employee.query.filter_by(name=new_name).first()
                if existing_employee:
                    flash(f"Employee name '{new_name}' already exists.", 'error')
                    return render_template('edit_employee.html', employee=employee)
            
            # Update the name
            employee.name = new_name
            
            # Check if a new photo was uploaded
            if photo:
                print("New photo uploaded. Replacing old photo.")
                # 1. Delete old photo file
                old_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(employee.photo_path))
                if os.path.exists(old_photo_path):
                    os.remove(old_photo_path)
                    
                # 2. Save new photo
                filename = secure_filename(photo.filename)
                unique_filename = str(uuid.uuid4()) + "_" + filename
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                db_path = os.path.join(UPLOAD_FOLDER_REL, unique_filename).replace("\\", "/")
                photo.save(save_path)
                
                # 3. Update photo path in database
                employee.photo_path = db_path

            # Commit changes to the database
            db.session.commit()
            
            # Re-run trainer
            print("Running trainer in background after edit...")
            trainer_script_path = os.path.join('face_recognition_module', 'trainer.py')
            os.system(f'python {trainer_script_path}')
            print("Training complete.")

            flash(f'Employee {employee.name} updated successfully.', 'success')
            return redirect(url_for('admin_dashboard'))

        except Exception as e:
            db.session.rollback()
            print(f"Error editing employee: {e}")
            flash('Error editing employee. Please check logs.', 'error')
            return render_template('edit_employee.html', employee=employee)

    # 3. If it's a GET request (page loaded)
    # Show the edit form with the employee's current data
    return render_template('edit_employee.html', employee=employee)


# 6. --- User Module (Public Pages) ---

@app.route('/')
def user_dashboard():
    try:
        # Get the search query from the URL (e.g., /?search=rohan)
        search_query = request.args.get('search', '') # Get 'search' parameter, default to empty string
        
        today = date.today()
        
        # Get today's attendance
        todays_attendance = Attendance.query.filter_by(date=today).all()
        present_employee_names = [record.employee.name for record in todays_attendance]
        
        # Get employees
        if search_query:
            # If there's a search, filter employees by name
            employees = Employee.query.filter(Employee.name.ilike(f'%{search_query}%')).all()
        else:
            # If no search, get all employees
            employees = Employee.query.all()
            
        return render_template('user_dashboard.html', 
                               employees=employees,
                               present_names=present_employee_names,
                               search_query=search_query,
                               today=today)
    except Exception as e:
        print(f"Error in user_dashboard route: {e}")
        return "An error occurred. Please check logs."



# 7. --- Run the App ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)



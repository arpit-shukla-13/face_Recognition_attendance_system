# trainer.py (Version 2 - Database Connected)

import face_recognition
import os
import pickle
import sys

# --- 1. Database Connection ---
print("Connecting to database...")


# This allows us to import 'app.py' and its models
parent_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(parent_dir)

try:
    # Import the app and database models
    from app import app, db, Employee
except ImportError as e:
    print(f"Error importing app: {e}")
    print("Please make sure 'app.py' exists in the parent directory.")
    exit()

# We will store the face encodings and corresponding names here
known_encodings = []
known_names = []

print("Training process started...")

# --- 2. Process Employees from Database ---
# We must run database queries within the app context
try:
    with app.app_context():
        # Get all employees from the database
        employees = Employee.query.all()
        
        if not employees:
            print("No employees found in the database. Please add employees via the web app first.")
            exit()
            
        print(f"Found {len(employees)} employee(s). Processing...")

        # Loop through each employee in the database
        for employee in employees:
            employee_name = employee.name
            relative_photo_path = employee.photo_path # e.g., 'uploads/employee_photos/uuid_photo.jpg'
            
            # Construct the absolute path to the image file
            # parent_dir = 'D:\employee_management_system'
            # static_path = 'static'
            # relative_photo_path = 'uploads/employee_photos/uuid_photo.jpg'
            # -> 'D:\employee_management_system\static\uploads\employee_photos\uuid_photo.jpg'
            image_path = os.path.join(parent_dir, 'static', relative_photo_path)

            print(f"Processing image for: {employee_name} (Path: {image_path})")
            
            if not os.path.exists(image_path):
                print(f"Warning: Photo not found at {image_path} for {employee_name}. Skipping.")
                continue

            # Load the image file
            image = face_recognition.load_image_file(image_path)
            
            # Find face encodings in the image.
            encodings = face_recognition.face_encodings(image)
            
            if encodings:
                # Take the first encoding found
                encoding = encodings[0]
                
                # Add the encoding and the *correct name from DB*
                known_encodings.append(encoding)
                known_names.append(employee_name)
            else:
                print(f"Warning: No face found in {relative_photo_path} for {employee_name}. Skipping.")
                
except Exception as e:
    print(f"An error occurred during database access or processing: {e}")
    exit()

# --- 3. Save Encodings to File ---
encodings_file_path = 'encodings.pickle'
print("\nSaving encodings to file...")
data = {"encodings": known_encodings, "names": known_names}

try:
    with open(encodings_file_path, "wb") as f:
        f.write(pickle.dumps(data))
    print(f"\nTraining complete. Encodings saved to '{encodings_file_path}'")
except Exception as e:
    print(f"Error saving pickle file: {e}") 
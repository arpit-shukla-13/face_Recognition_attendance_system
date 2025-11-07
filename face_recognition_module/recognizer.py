# recognizer.py (Version 2 - Database Connected)

import face_recognition
import cv2
import os
import pickle
import sys
from datetime import date

# --- 1. Database Connection ---
print("Connecting to database...")

# Add the parent directory (main project folder) to the system path
parent_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(parent_dir)

try:
    # Import the app, db, and models
    from app import app, db, Employee, Attendance
except ImportError as e:
    print(f"Error importing app: {e}")
    exit()

# We need to run database operations within the Flask app context
app_context = app.app_context()
app_context.push()

print("Database connected.")

# --- 2. Load the known faces and encodings ---
encodings_file_path = 'encodings.pickle'
print(f"Loading encodings from {encodings_file_path}...")
try:
    data = pickle.loads(open(encodings_file_path, "rb").read())
    known_encodings = data["encodings"]
    known_names = data["names"]
    print("Encodings loaded successfully.")
except FileNotFoundError:
    print(f"Error: Encodings file '{encodings_file_path}' not found.")
    print("Please run trainer.py first.")
    app_context.pop() # Clean up context before exiting
    exit()

# --- 3. Initialize the Webcam ---

# Trying camera index 1 instead of 0
video_capture = cv2.VideoCapture(1)
# === END OF FIX ===



# Check if camera opened successfully
if not video_capture.isOpened():
    print("Error: Could not open camera at index 1. Trying index 0...")
    video_capture = cv2.VideoCapture(0) # Fallback to 0
    if not video_capture.isOpened():
        print("Error: Could not open camera at index 0 either.")
        print("Please check if camera is connected and not used by another app.")
        app_context.pop()
        exit()

print("Webcam started. Press 'q' to quit.")

# --- 4. Initialize variables for attendance ---
already_marked_today = set()

# Load names of already marked employees for today
try:
    today = date.today()
    attendances = Attendance.query.filter_by(date=today).all()
    for att in attendances:
        already_marked_today.add(att.employee.name)
    print(f"Already marked today: {already_marked_today}")
except Exception as e:
    print(f"Error fetching today's attendance: {e}")
    

# --- 5. Start the real-time recognition loop ---
while True:
    ret, frame = video_capture.read()
    if not ret:
        print("Error: Failed to grab frame from webcam.")
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        
        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.6)
        name = "Unknown"

        face_distances = face_recognition.face_distance(known_encodings, face_encoding)
        if True in matches:
            best_match_index = face_distances.argmin()
            name = known_names[best_match_index]

        # --- 6. Mark Attendance Logic ---
        if name != "Unknown":
            if name not in already_marked_today:
                try:
                    employee = Employee.query.filter_by(name=name).first()
                    if employee:
                        new_attendance = Attendance(employee_id=employee.id, date=date.today())
                        db.session.add(new_attendance)
                        db.session.commit()
                        already_marked_today.add(name)
                        print(f"*** Attendance MARKED for {name} ***")
                    
                except Exception as e:
                    print(f"Error marking attendance for {name}: {e}")
                    db.session.rollback()

        # --- 7. Draw boxes and display the name ---
        color = (0, 0, 255) # Red for Unknown
        if name != "Unknown":
            color = (0, 255, 0) # Green for Known
            if name in already_marked_today:
                color = (0, 255, 255) # Yellow if already marked

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (0, 0, 0), 1) # Black text

    # --- 8. Display the final image ---
    cv2.imshow('Video', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- 9. Release the webcam and close windows ---
print("Stopping recognizer...")
video_capture.release()
cv2.destroyAllWindows()
app_context.pop() # Clean up the app context
print("Shutdown complete.")

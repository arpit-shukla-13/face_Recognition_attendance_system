Employee Attendance System with Face Recognition

This is a full-stack web application built with Python and Flask that manages and tracks employee attendance using real-time face recognition.

Features

This project consists of three main modules:

1. Admin Module (Secure Dashboard)

Secure Signup/Login: A separate, password-protected account and login system for administrators (using password hashing).

Employee Management (CRUD):

Create: Add new employees with their name and photo.

Read: View a list of all registered employees.

Update: Edit an employee's name or update their photo.

Delete: Completely remove an employee from the system.

Live Attendance Dashboard: A real-time dashboard to see which employees are "Present" or "Absent" for the day.

Automatic AI Training: The AI model (encodings.pickle) is automatically updated (retrained) in the background whenever an employee is added, edited, or deleted.

2. User Module (Public Dashboard)

Live Status: The main website (/) provides a public dashboard showing a list of all employees and their live attendance status (Present/Absent).

Search Functionality: Quickly find any employee by searching for their name.

3. Face Recognition Kiosk (Attendance Module)

This is a separate script (recognizer.py) designed to run at an office entrance.

Real-time Recognition: Uses the webcam to detect and identify faces in a live video feed.

Automatic Marking: Marks the identified employee's attendance directly in the database.

Duplicate Prevention: An employee's attendance is marked only once per day (indicated by a yellow box on subsequent recognitions).

Technology Stack

Backend: Python, Flask, Flask-SQLAlchemy

Database: SQLite

Face Recognition: face_recognition (based on dlib), OpenCV (cv2)

Frontend: HTML, CSS

Security: Werkzeug (Password Hashing), Flask Session

Setup and Installation

Follow these steps to set up the project on a new system:

Clone the Repository:

git clone [https://github.com/your-username/your-repository-name.git](https://github.com/your-username/your-repository-name.git)
cd your-repository-name


Prerequisites (Crucial):
The face_recognition library requires dlib. Before installing, you MUST have CMake and C++ build tools installed on your system.

On Windows:

Install Visual Studio Build Tools (Select "Desktop development with C++" during installation).

Install CMake (Ensure you check "Add CMake to the system PATH for all users" during installation).

Create Virtual Environment:
Create and activate a virtual environment.

# Create a new environment named 'venv'
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate


Install Dependencies:
Install all required libraries from the requirements.txt file.

pip install -r requirements.txt


How to Run the Project

This project requires two separate terminals to run simultaneously (both must have the venv activated).

Terminal 1: Start the Web Server (Website)

This terminal will run your Flask website (Admin and User Dashboards).

# (venv) D:\employee_management_system>
python app.py


The server will start on http://127.0.0.1:5000.

Keep this terminal running.

Terminal 2: Start the Face Recognition (Kiosk)

This terminal will run the camera and mark attendance.

# (venv) D:\employee_management_system>
cd face_recognition_module
python recognizer.py


Your webcam will turn on.

Keep this terminal running.

Your system is now fully operational.



📘 Smart Student Management System Using NFC Technology
📌 Overview
The NFC Student Management System is a Django-based web application developed to streamline student management processes for various roles,
including Registrar, Gatekeeper, Teacher, and Finance Staff. It integrates NFC (Near Field Communication) technology to improve efficiency 
in tracking student attendance and managing student profiles.

🚀 Key Features
🔐 Registrar Portal
•	Student Registration:
•	Register students with detailed information such as campus, college, school, department, class, and NFC card URL.
•	Dynamic field filtering (e.g., colleges based on campus, schools based on college, etc.).
•	Student Management:
•	View and manage all registered students.
•	Filter by campus, college, school, department, and class.
🛂 Gatekeeper Portal
•	NFC Card Scanning:
•	Quickly scan NFC cards to retrieve student profiles.
•	View-Only Access:
•	Gatekeepers can view student profiles but cannot see financial or attendance data.
•	Access Control:
•	Only authenticated gatekeepers can use this portal.
🎓 Teacher Portal
•	Attendance Tracking:
•	Record attendance for both classes and exams.
•	Attendance can be taken via NFC scan.
•	Reports:
•	Export attendance reports in PDF format.
•	View lists of both present and absent students.
•	Filtering:
•	Filter students by department and class before taking attendance.
💰 Finance Portal
•	Payment Management:
•	View all students and their payment statuses.
•	Update payment status (Paid, Unpaid, Pending).
•	Filtering:
•	Filter students by payment status, department, and class.
•	Profile Access:
•	Finance staff can see payment-related student details, but not academic or attendance records.
•	Reports: Export Payment PDF reports

⚙️ Technical Highlights
•	Django Framework: Built on Django with full use of its ORM, authentication system, and templating engine.
•	NFC Integration: Simulates card scanning via a utility function (scan_nfc_card), ready for real hardware integration.
•	Dynamic Filtering: Implements AJAX-based dependent dropdowns for registration forms.
•	Role-Based Access Control: Uses custom decorators to restrict access based on user roles.
•	PDF Report Generation: Generates downloadable attendance reports using the ReportLab library.
•	Responsive Design: Basic HTML templates provided, with potential for enhancement via CSS frameworks like Bootstrap or Tailwind.


🧱 Project Structure
•	Models: Campus, College, School, Department, Class, Student, Attendance
•	Forms: StudentRegistrationForm, AttendanceFilterForm, FinanceFilterForm, RegistrarFilterForm, PaymentStatusForm
•	Views: Each role has its own dashboard and functionality
•	Templates: Separate HTML templates for every user role and feature

🛠️ Getting Started
1. Clone the Repository
git clone <repository-url>
cd nfc_student_management
2. Set Up a Virtual Environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
3. Install Dependencies
pip install -r requirements.txt
4. Apply Migrations
python manage.py makemigrations
python manage.py migrate
5. Run the Server
python manage.py runserver
6. Access the App
Open your browser and go to http://127.0.0.1:8000/

📄 License
This project is licensed under the MIT License





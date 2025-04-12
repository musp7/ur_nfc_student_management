## filepath: core/views.py
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404 , redirect 
from .models import Student, Attendance
from accounts.decorators import role_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import StudentRegistrationForm
from .forms import AttendanceForm
from .forms import AttendanceFilterForm
from .nfc_utils import scan_nfc_card
from accounts.models import CustomUser
import pandas as pd
from .models import College, School, Department, Class
from .forms import PaymentStatusForm
from .forms import FinanceFilterForm

@login_required
@role_required(['admin', 'gatekeeper', 'registrar'])  # Allow these roles
def student_profile(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    return render(request, 'core/student_profile.html', {'student': student})





def landing_page(request):
    """
    Displays the landing page with links to all portals.
    """
    return render(request, 'core/landing_page.html')




@login_required
@role_required(['gatekeeper'])
def gatekeeper_dashboard(request):
    """
    Gatekeeper dashboard view.
    """
    return render(request, 'core/gatekeeper_dashboard.html')
# @login_required
# @role_required('teacher')
# def teacher_dashboard(request):
#     return HttpResponse("core/teacher_dashboard.html")
@login_required
@role_required(['teacher'])
def teacher_dashboard(request):
    """
    Teacher dashboard view.
    """
    return render(request, 'core/teacher_dashboard.html')

# @login_required
# @role_required('registrar')
# def registrar_dashboard(request):
#     return HttpResponse("core/registrar_dashboard.html")
@login_required
@role_required(['registrar'])
def registrar_dashboard(request):
    """
    Registrar dashboard view.
    """
    return render(request, 'core/registrar_dashboard.html')

@login_required
@role_required('finance')
def finance_dashboard(request):
    return HttpResponse("core/finance_dashboard.html")

@login_required
@role_required(['registrar'])
def register_student(request):
    """
    View for registering a new student.
    """
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)
            student.payment_status = 'PENDING'  # Set default payment status
            student.save()
            return redirect('registrar-dashboard')
    else:
        form = StudentRegistrationForm()
    return render(request, 'core/register_student.html', {'form': form})

@login_required
@role_required(['registrar'])
def view_all_students(request):
    """
    View for displaying all registered students.
    """
    students = Student.objects.all()  # Fetch all students from the database
    return render(request, 'core/view_all_students.html', {'students': students})


# @login_required
# @role_required(['teacher'])
# def take_attendance(request):
#     """
#     View for taking attendance.
#     """
#     students = None
#     attended_students = []
#     form = AttendanceFilterForm()  # Initialize the form by default

#     if request.method == 'POST':
#         if 'filter_students' in request.POST:  # Filter students
#             form = AttendanceFilterForm(request.POST)
#             if form.is_valid():
#                 department = form.cleaned_data['department']
#                 level = form.cleaned_data['level']
#                 attendance_type = form.cleaned_data['attendance_type']

#                 # Filter students based on department and level
#                 students = Student.objects.all()
#                 if department:
#                     students = students.filter(department=department)
#                 if level:
#                     students = students.filter(student_class=level)

#                 # Save attendance type in session for NFC scanning
#                 request.session['attendance_type'] = attendance_type

#         elif 'scan_nfc' in request.POST:  # Scan NFC card
#             try:
#                 student_id = scan_nfc_card()  # Scan the NFC card
#                 student = Student.objects.get(student_id=student_id)
#                 attendance_type = request.session.get('attendance_type')

#                 # Record attendance
#                 Attendance.objects.create(
#                     student=student,
#                     teacher=request.user,
#                     attendance_type=attendance_type
#                 )
#                 attended_students.append(student)
#             except Exception as e:
#                 return render(request, 'core/take_attendance.html', {
#                     'form': form,
#                     'students': students,
#                     'error': str(e)
#                 })

#         elif 'end_attendance' in request.POST:  # End attendance
#             # Fetch attended students from the database
#             attendance_type = request.session.get('attendance_type')
#             attended_students = Attendance.objects.filter(
#                 teacher=request.user,
#                 attendance_type=attendance_type
#             ).select_related('student')

#     return render(request, 'core/take_attendance.html', {
#         'form': form,
#         'students': students,
#         'attended_students': attended_students,
#     })

@login_required
@role_required(['teacher'])
def take_attendance(request):
    """
    View for taking attendance.
    """
    students = None
    attended_students = []
    form = AttendanceFilterForm(request.POST or None)  # Initialize the form with POST data if available

    if request.method == 'POST':
        if 'filter_students' in request.POST:  # Filter students
            if form.is_valid():
                department = form.cleaned_data['department']
                level = form.cleaned_data['level']
                attendance_type = form.cleaned_data['attendance_type']

                # Filter students based on department and level
                students = Student.objects.all()
                if department:
                    students = students.filter(department=department)
                if level:
                    students = students.filter(student_class=level)

                # Save attendance type and filtered students in session for persistence
                request.session['attendance_type'] = attendance_type
                request.session['filtered_students'] = list(students.values_list('id', flat=True))

        elif 'scan_nfc' in request.POST:  # Scan NFC card
            try:
                student_id = scan_nfc_card()  # Scan the NFC card
                student = Student.objects.get(student_id=student_id)
                attendance_type = request.session.get('attendance_type')

                # Record attendance
                Attendance.objects.create(
                    student=student,
                    teacher=request.user,
                    attendance_type=attendance_type
                )
                attended_students.append(student)
            except Exception as e:
                return render(request, 'core/take_attendance.html', {
                    'form': form,
                    'students': students,
                    'error': str(e)
                })

        elif 'end_attendance' in request.POST:  # End attendance and generate report
            # Restore filtered students from the session
            filtered_student_ids = request.session.get('filtered_students', [])
            students = Student.objects.filter(id__in=filtered_student_ids)

            # Fetch attended students from the database
            attendance_type = request.session.get('attendance_type')
            attended_students = Attendance.objects.filter(
                teacher=request.user,
                attendance_type=attendance_type
            ).select_related('student')

            # Generate attendance report
            response = generate_attendance_report(students, attended_students)
            return response

    return render(request, 'core/take_attendance.html', {
        'form': form,
        'students': students,
        'attended_students': attended_students,
    })


def generate_attendance_report(filtered_students, attended_students):
    """
    Generate a CSV attendance report for the filtered students.
    """
    # Create a list of attended student IDs
    attended_student_ids = [attendance.student.id for attendance in attended_students]

    # Prepare data for the report
    report_data = []
    for student in filtered_students:
        report_data.append({
            'Student ID': student.student_id,
            'First Name': student.first_name,
            'Last Name': student.last_name,
            'Attendance Status': 'Attended' if student.id in attended_student_ids else 'Absent'
        })

    # Create a DataFrame using pandas
    df = pd.DataFrame(report_data)

    # Generate a CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_report.csv"'
    df.to_csv(path_or_buf=response, index=False)
    return response

def load_colleges(request):
    campus_id = request.GET.get('campus_id')
    colleges = College.objects.filter(campus_id=campus_id).order_by('name')
    return render(request, 'core/dropdown_list_options.html', {'options': colleges})

def load_schools(request):
    college_id = request.GET.get('college_id')
    schools = School.objects.filter(college_id=college_id).order_by('name')
    return render(request, 'core/dropdown_list_options.html', {'options': schools})

def load_departments(request):
    school_id = request.GET.get('school_id')
    departments = Department.objects.filter(school_id=school_id).order_by('name')
    return render(request, 'core/dropdown_list_options.html', {'options': departments})

def load_classes(request):
    department_id = request.GET.get('department_id')
    classes = Class.objects.filter(department_id=department_id).order_by('name')
    return render(request, 'core/dropdown_list_options.html', {'options': classes})

@login_required
@role_required(['gatekeeper'])
def scan_card(request):
    """
    View for scanning NFC cards and loading student profiles.
    """
    student = None
    error = None

    if request.method == 'POST':
        try:
            # Simulate NFC card scanning
            student_id = scan_nfc_card()  # Replace with actual NFC scanning logic
            student = get_object_or_404(Student, student_id=student_id)
        except Exception as e:
            error = str(e)

    return render(request, 'core/scan_card.html', {'student': student, 'error': error})

# filepath: core/views.py

@login_required
@role_required(['gatekeeper'])
def scan_card(request):
    """
    View for scanning NFC cards and loading student profiles.
    """
    student = None
    error = None

    if request.method == 'POST':
        try:
            # Simulate NFC card scanning
            student_id = scan_nfc_card()  # Replace with actual NFC scanning logic
            student = get_object_or_404(Student, student_id=student_id)
        except Exception as e:
            error = str(e)

    # Exclude sensitive information
    if student:
        student.payment_status = None  # Hide financial status
        student.attendance_records = None  # Hide attendance records (if applicable)

    return render(request, 'core/scan_card.html', {'student': student, 'error': error})

@login_required
@role_required(['finance'])
def finance_dashboard(request):
    """
    Finance dashboard view with filtering functionality.
    """
    students = Student.objects.all()  # Fetch all registered students
    form = FinanceFilterForm(request.GET or None)

    if form.is_valid():
        # Filter by payment status
        payment_status = form.cleaned_data.get('payment_status')
        if payment_status:
            students = students.filter(payment_status=payment_status)

        # Filter by department
        department = form.cleaned_data.get('department')
        if department:
            students = students.filter(department=department)

        # Filter by class
        student_class = form.cleaned_data.get('student_class')
        if student_class:
            students = students.filter(student_class=student_class)

    return render(request, 'core/finance_dashboard.html', {'students': students, 'form': form})

@login_required
@role_required(['finance'])
def finance_student_detail(request, student_id):
    """
    View for finance staff to view and update a student's payment status.
    """
    student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        form = PaymentStatusForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('finance-dashboard')
    else:
        form = PaymentStatusForm(instance=student)

    return render(request, 'core/finance_student_detail.html', {'student': student, 'form': form})
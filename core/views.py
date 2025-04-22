## filepath: core/views.py
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404 , redirect 
from django.contrib import messages
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
from .forms import RegistrarFilterForm
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch


@login_required
@role_required(['admin', 'gatekeeper', 'registrar','teacher'])  # Allow these roles
def student_profile(request, student_id):
    """
    View to display a student's profile and mark attendance if applicable.
    """
    student = get_object_or_404(Student, student_id=student_id)

    # Check if the student is among the filtered students for the current session
    filtered_student_ids = request.session.get('filtered_students', [])
    attendance_type = request.session.get('attendance_type')

    if student.id in filtered_student_ids:
        # Mark the student as present
        Attendance.objects.get_or_create(
            student=student,
            teacher=request.user,
            attendance_type=attendance_type
        )

    return render(request, 'core/student_profile.html', {
        'student': student,
    })
# def student_profile(request, student_id):
#      student = get_object_or_404(Student, student_id=student_id)
#      return render(request, 'core/student_profile.html', {'student': student})





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
    Registrar dashboard view with options to register a new student and view/filter registered students.
    """
    # Handle student registration
    if request.method == 'POST' and 'register_student' in request.POST:
        registration_form = StudentRegistrationForm(request.POST, request.FILES)
        if registration_form.is_valid():
            registration_form.save()
            return redirect('registrar-dashboard')
    else:
        registration_form = StudentRegistrationForm()

    # Handle filtering of registered students
    students = Student.objects.all()
    filter_form = RegistrarFilterForm(request.GET or None)

    if filter_form.is_valid():
        # Filter by campus
        campus = filter_form.cleaned_data.get('campus')
        if campus:
            students = students.filter(campus=campus)

        # Filter by college
        college = filter_form.cleaned_data.get('college')
        if college:
            students = students.filter(college=college)

        # Filter by school
        school = filter_form.cleaned_data.get('school')
        if school:
            students = students.filter(school=school)

        # Filter by department
        department = filter_form.cleaned_data.get('department')
        if department:
            students = students.filter(department=department)

        # Filter by class
        student_class = filter_form.cleaned_data.get('student_class')
        if student_class:
            students = students.filter(student_class=student_class)

    return render(request, 'core/registrar_dashboard.html', {
        'registration_form': registration_form,
        'filter_form': filter_form,
        'students': students,
    })

@login_required
@role_required('finance')
def finance_dashboard(request):
    return HttpResponse("core/finance_dashboard.html")

@login_required
@role_required(['registrar'])
def registrar_dashboard(request):
    """
    Registrar dashboard view with options to register a new student.
    """
    # Handle student registration
    if request.method == 'POST' and 'register_student' in request.POST:
        registration_form = StudentRegistrationForm(request.POST, request.FILES)
        if registration_form.is_valid():
            registration_form.save()
            return redirect('registrar-dashboard')
    else:
        registration_form = StudentRegistrationForm()

    return render(request, 'core/registrar_dashboard.html', {
        'registration_form': registration_form,
    })

@login_required
@role_required(['registrar'])
def view_all_students(request):
    """
    View for displaying all registered students.
    """
    students = Student.objects.all()  # Fetch all students from the database
    return render(request, 'core/view_all_students.html', {'students': students})







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

@csrf_exempt
@login_required
@role_required(['teacher'])
def scan_nfc(request):
    """
    Handle NFC card scanning via AJAX.
    """
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        attendance_type = request.session.get('attendance_type')

        try:
            student = Student.objects.get(student_id=student_id)
            # Record attendance
            Attendance.objects.create(
                student=student,
                teacher=request.user,
                attendance_type=attendance_type
            )
            return JsonResponse({'message': f"Student {student.student_id} is scanned successfully."})
        except Student.DoesNotExist:
            return JsonResponse({'error': "Student not found."}, status=404)

    return JsonResponse({'error': "Invalid request method."}, status=400)


# def generate_attendance_report(filtered_students, attended_students):
#     """
#     Generate a CSV attendance report for the filtered students with a detailed header.
#     """
#     # Create a set of attended student IDs for faster lookup
#     attended_student_ids = {attendance.student.id for attendance in attended_students}

#     # Prepare data for the report
#     report_data = []
#     for student in filtered_students:
#         report_data.append({
#             'Student ID': student.student_id,
#             'First Name': student.first_name,
#             'Last Name': student.last_name,
#             'Attendance Status': 'Attended' if student.id in attended_student_ids else 'Absent'
#         })

#     # Extract additional details for the header
#     if attended_students:
#         teacher = attended_students[0].teacher
#         teacher_name = teacher.get_full_name() if teacher.get_full_name() else teacher.username
#         attendance_type = attended_students[0].attendance_type
#         date = attended_students[0].timestamp.strftime('%Y-%m-%d')
#     else:
#         teacher_name = "N/A"
#         attendance_type = "N/A"
#         date = "N/A"

#     department = filtered_students[0].department.name if filtered_students else "N/A"
#     student_class = filtered_students[0].student_class.name if filtered_students else "N/A"

#     # Generate a CSV response
#     response = HttpResponse(content_type='text/csv')
#     response['Content-Disposition'] = 'attachment; filename="attendance_report.csv"'

#     # Write the header details
#     response.write(f"Attendance Type: {attendance_type}\n")
#     response.write(f"Department: {department}\n")
#     response.write(f"Class: {student_class}\n")
#     response.write(f"Date: {date}\n")
#     response.write(f"Teacher: {teacher_name}\n\n")

#     # Write the student attendance data
#     df = pd.DataFrame(report_data)
#     df.to_csv(path_or_buf=response, index=False)
#     return response

def generate_attendance_report(filtered_students, attended_students):
    """
    Generate a PDF attendance report for the filtered students with a detailed header.
    """

    # Create a set of attended student IDs
    attended_student_ids = {attendance.student.id for attendance in attended_students}

    # Get teacher, date, and attendance type info (if available)
    if attended_students:
        teacher = attended_students[0].teacher
        teacher_name = teacher.get_full_name() or teacher.username
        attendance_type = attended_students[0].attendance_type
        date = attended_students[0].timestamp.strftime('%Y-%m-%d')
    else:
        teacher_name = "N/A"
        attendance_type = "N/A"
        date = "N/A"

    department = filtered_students[0].department.name if filtered_students else "N/A"
    student_class = filtered_students[0].student_class.name if filtered_students else "N/A"

    # Prepare PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="attendance_report.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y = height - inch

    # Header section
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, y, "Attendance Report")
    y -= 20

    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Attendance Type: {attendance_type}")
    y -= 15
    p.drawString(50, y, f"Department: {department}")
    y -= 15
    p.drawString(50, y, f"Class: {student_class}")
    y -= 15
    p.drawString(50, y, f"Date: {date}")
    y -= 15
    p.drawString(50, y, f"Teacher: {teacher_name}")
    y -= 30

    # Table headers
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "Student ID")
    p.drawString(150, y, "First Name")
    p.drawString(250, y, "Last Name")
    p.drawString(350, y, "Status")
    y -= 20

    # Student data
    p.setFont("Helvetica", 10)
    for student in filtered_students:
        if y < 50:  # Create new page if running out of space
            p.showPage()
            y = height - inch
        status = "Attended" if student.id in attended_student_ids else "Absent"
        p.drawString(50, y, str(student.student_id))
        p.drawString(150, y, student.first_name)
        p.drawString(250, y, student.last_name)
        p.drawString(350, y, status)
        y -= 15

    p.showPage()
    p.save()

    return response


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

@login_required
@role_required(['registrar'])
def registered_students(request):
    """
    View to display all registered students with filtering functionality.
    """
    students = Student.objects.all()
    filter_form = RegistrarFilterForm(request.GET or None)

    if filter_form.is_valid():
        # Filter by campus
        campus = filter_form.cleaned_data.get('campus')
        if campus:
            students = students.filter(campus=campus)

        # Filter by college
        college = filter_form.cleaned_data.get('college')
        if college:
            students = students.filter(college=college)

        # Filter by school
        school = filter_form.cleaned_data.get('school')
        if school:
            students = students.filter(school=school)

        # Filter by department
        department = filter_form.cleaned_data.get('department')
        if department:
            students = students.filter(department=department)

        # Filter by class
        student_class = filter_form.cleaned_data.get('student_class')
        if student_class:
            students = students.filter(student_class=student_class)

    return render(request, 'core/registered_students.html', {
        'students': students,
        'filter_form': filter_form,
    })






@login_required
@role_required(['registrar'])
def register_student(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            messages.success(request, f'Thank you for registering {student.first_name} {student.last_name}!')
            return redirect('registrar-dashboard')
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'core/register_student.html', {'form': form})

@login_required
@role_required(['registrar'])
def edit_student(request, student_id):
    """
    View to edit a single student's details.
    """
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f"Student {student.first_name} {student.last_name} updated successfully.")
            return redirect('registered-students')
    else:
        form = StudentRegistrationForm(instance=student)

    return render(request, 'core/edit_student.html', {'form': form, 'student': student})

# @login_required
# @role_required(['registrar'])
# def edit_students(request):
#     """
#     View to bulk edit students' class.
#     """
#     student_ids = request.GET.get('ids', '').split(',')
#     students = Student.objects.filter(id__in=student_ids)

#     if request.method == 'POST':
#         new_class = request.POST.get('student_class')
#         if new_class:
#             students.update(student_class=new_class)
#             messages.success(request, "Selected students' class updated successfully.")
#             return redirect('registered-students')
#     return render(request, 'core/edit_students.html', {'students': students})

@login_required
@role_required(['registrar'])
def edit_students(request):
    """
    View to bulk edit students' class.
    """
    student_ids = request.GET.get('ids', '').split(',')
    students = Student.objects.filter(id__in=student_ids)

    # Get classes - modified code goes here
    classes = Class.objects.none()  # Default empty queryset
    if students.exists():
        # Assuming all selected students are from the same department
        department = students.first().department
        if department:  # Check if department exists
            classes = Class.objects.filter(department=department).order_by('name')

    if request.method == 'POST':
        new_class_id = request.POST.get('student_class')
        if new_class_id:
            new_class = Class.objects.get(id=new_class_id)
            students.update(student_class=new_class)
            messages.success(request, "Selected students' class updated successfully.")
            return redirect('registered-students')

    return render(request, 'core/edit_students.html', {
        'students': students,
        'classes': classes,
    })

@login_required
@role_required(['registrar'])
def delete_students(request):
    """
    View to delete selected students.
    """
    if request.method == 'POST':
        student_ids = request.POST.getlist('selected_students')
        Student.objects.filter(id__in=student_ids).delete()
        messages.success(request, "Selected students deleted successfully.")
        return redirect('registered-students')
    

## filepath: core/views.py
import csv
from datetime import datetime
from multiprocessing import Value
from django.forms import IntegerField
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import When, Case, Count, Q
from django.shortcuts import render, get_object_or_404 , redirect 
from django.contrib import messages

from accounts import models
from .models import Student, Attendance, StudentEntry
from accounts.decorators import role_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import HttpResponse
from .forms import StudentRegistrationForm
from .forms import AttendanceForm
from .forms import AttendanceFilterForm
from .nfc_utils import scan_nfc_card
from accounts.models import CustomUser
import pandas as pd

from .models import College, School, Department, Class,Campus
from .forms import PaymentStatusForm
from .forms import FinanceFilterForm
from .forms import RegistrarFilterForm
from django.urls import reverse
import pytz
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from io import BytesIO
from reportlab.lib.styles import getSampleStyleSheet


@login_required
@role_required(['admin', 'gatekeeper', 'registrar','teacher'])
def student_profile(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    attendance_type = request.GET.get('attendance_type') or request.session.get('attendance_type')
    is_modal = request.GET.get('modal', 'false').lower() == 'true'
    portal_message = None
    kigali_tz = pytz.timezone('Africa/Kigali')

    # Gatekeeper functionality (unchanged)
    if request.user.role == 'gatekeeper':
        last_entry = StudentEntry.objects.filter(
            student=student,
            exit_time__isnull=True
        ).order_by('-entry_time').first()
        
        if last_entry:
            
            last_entry.exit_time = timezone.now().astimezone(kigali_tz)
            last_entry.save()
            portal_message = f"{student.first_name} has exited at {last_entry.exit_time.strftime('%H:%M:%S')}"
        else:
            StudentEntry.objects.create(
                student=student,
                gatekeeper=request.user
            )
            portal_message = f"Welcome {student.first_name}! Entry recorded at {timezone.now().astimezone(kigali_tz).strftime('%H:%M:%S')}"
    
    # Teacher attendance tracking (unchanged)
    elif request.user.role == 'teacher' and attendance_type:
        if not Attendance.objects.filter(
            student=student,
            teacher=request.user,
            attendance_type=attendance_type
        ).exists():
            Attendance.objects.create(
                student=student,
                teacher=request.user,
                attendance_type=attendance_type
            )
            
            if attendance_type == 'CLASS':
                portal_message = f"Class attendance recorded for {student.first_name}"
            elif attendance_type == 'EXAM_START':
                portal_message = f"Exam started for {student.first_name} at {timezone.now().strftime('%H:%M:%S')}"
            elif attendance_type == 'EXAM_END':
                portal_message = f"Exam submitted by {student.first_name} at {timezone.now().strftime('%H:%M:%S')}"
    
    # Check if request is from WebSocket (unchanged)
    is_websocket = request.headers.get('Upgrade', '').lower() == 'websocket'
    
    # Prepare context data
    context = {
        'student': student,
        'attendance_type': attendance_type if request.user.role == 'teacher' else None,
        'portal_message': portal_message,
        'hide_financial': request.user.role == 'gatekeeper',
    }
    
    # If WebSocket request, return JSON response (unchanged)
    if is_websocket:
        from django.http import JsonResponse
        student_data = {
            'id': student.student_id,
            'name': f"{student.first_name} {student.last_name}",
            'photo_url': student.photo.url if student.photo else None,
            'department': student.department.name if student.department else None,
            'class': student.student_class.name if student.student_class else None,
            'laptop_model': student.laptop_model or "Not specified",
            'laptop_serial': student.laptop_serial or "Not specified",
            'message': portal_message,
        }
        
        if request.user.role != 'gatekeeper':
            student_data['payment_status'] = student.get_payment_status_display()
            student_data['payment_badge_class'] = 'bg-success' if student.payment_status == 'PAID' else 'bg-danger' if student.payment_status == 'UNPAID' else 'bg-warning'
        
        return JsonResponse(student_data)
    
    # If modal request, return modal template
    if is_modal:
        return render(request, 'core/student_profile_modal.html', context)
    
    return render(request, 'core/student_profile.html', context)





def landing_page(request):
   
    #Displays the landing page with links to all portals.
    
    return render(request, 'core/landing_page.html')






@login_required
@role_required(['gatekeeper'])
def gatekeeper_dashboard(request):

    
    # Get current time
    kigali_tz = pytz.timezone('Africa/Kigali')
    timezone_now = timezone.now().astimezone(kigali_tz)
    
    
    # Get filter parameters
    date_str = request.GET.get('date', '')
    department_id = request.GET.get('department', '')
    class_id = request.GET.get('class', '')
    if request.method == 'POST' and 'search_student' in request.POST:
        student_id = request.POST.get('student_id')
        try:
            student = Student.objects.select_related(
                'department', 'student_class', 'campus'
            ).get(student_id=student_id)
            
            # Check if student is currently in campus
            last_entry = StudentEntry.objects.filter(
                student=student,
                exit_time__isnull=True
            ).order_by('-entry_time').first()
            
            return render(request, 'core/gatekeeper_dashboard.html', {
                # Your existing context
                'searched_student': student,
                'current_status': 'IN' if last_entry else 'OUT',
                'last_entry_time': last_entry.entry_time if last_entry else None,
                # Include all your existing context variables
            })
            
        except Student.DoesNotExist:
            messages.error(request, "Student not found. Please check the ID and try again.")
        except Exception as e:
            messages.error(request, f"Error searching student: {str(e)}")
    
    # Handle manual entry/exit confirmation
    elif request.method == 'POST' and 'confirm_entry' in request.POST:
        student_id = request.POST.get('student_id')
        try:
            student = Student.objects.get(student_id=student_id)
            last_entry = StudentEntry.objects.filter(
                student=student,
                exit_time__isnull=True
            ).order_by('-entry_time').first()
            
            if last_entry:
                last_entry.exit_time = timezone_now
                last_entry.save()
                messages.success(request, f"{student} exited at {last_entry.exit_time.strftime('%H:%M:%S')}")
            else:
                StudentEntry.objects.create(
                    student=student,
                    gatekeeper=request.user,
                    entry_time=timezone_now
                )
                messages.success(request, f"{student} entered at {timezone_now.strftime('%H:%M:%S')}")
            
            return redirect('gatekeeper-dashboard')
            
        except Exception as e:
            messages.error(request, f"Error processing entry: {str(e)}")
    # Date handling
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone_now.date()
    except ValueError:
        selected_date = timezone_now.date()
    
    # Base query
    entries = StudentEntry.objects.filter(
        entry_time__date=selected_date
    ).select_related(
        'student', 
        'student__department', 
        'student__student_class'
    ).order_by('-entry_time')
    
    # Apply filters
    if department_id:
        entries = entries.filter(student__department_id=department_id)
    if class_id:
        entries = entries.filter(student__student_class_id=class_id)
    
    # Get filter options
    departments = Department.objects.all()
    classes = Class.objects.all()
    if department_id:
        classes = classes.filter(department_id=department_id)
    
    context = {
        'entries': entries,
        'selected_date': selected_date,
        'total_entries': entries.count(),
        'current_in_school': entries.filter(exit_time__isnull=True).count(),
        'checked_out_count': entries.filter(exit_time__isnull=False).count(),
        'timezone_now': timezone_now,
        'departments': departments,
        'classes': classes,
        'selected_department': int(department_id) if department_id else '',
        'selected_class': int(class_id) if class_id else '',
    }
    return render(request, 'core/gatekeeper_dashboard.html', context)

@login_required
@role_required(['gatekeeper'])
def scan_card(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        if not student_id:
            messages.error(request, "No student ID provided")
            return redirect('scan-card')
        
        try:
            student = get_object_or_404(Student, student_id=student_id)
            current_time = timezone.now() if hasattr(timezone, 'now') else datetime.now()
            
            last_entry = StudentEntry.objects.filter(
                student=student,
                exit_time__isnull=True
            ).order_by('-entry_time').first()
            
            if last_entry:
                last_entry.exit_time = current_time
                last_entry.save()
                messages.success(request, f"{student} exited at {last_entry.exit_time.strftime('%H:%M:%S')}")
            else:
                StudentEntry.objects.create(
                    student=student,
                    entry_time=current_time,
                    gatekeeper=request.user
                )
                messages.success(request, f"{student} entered at {current_time.strftime('%H:%M:%S')}")
            
            return redirect('gatekeeper-dashboard')
            
        except Exception as e:
            messages.error(request, f"Error processing card: {str(e)}")
            return redirect('scan-card')
    
    return render(request, 'core/scan_card.html')



@login_required
@role_required(['teacher'])
def teacher_dashboard(request):
    
    #Teacher dashboard view.
    
    return render(request, 'core/teacher_dashboard.html')


@login_required
@role_required(['registrar'])
def registrar_dashboard(request):
    
    #Registrar dashboard view with options to register a new student and view/filter registered students.
    
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
@role_required(['finance'])
def finance_dashboard(request):
    
    #Finance dashboard view with filtering functionality.
    
    students = Student.objects.all().select_related('department', 'student_class')
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

        # Filter by class - should only show classes from selected department
        student_class = form.cleaned_data.get('student_class')
        if student_class:
            students = students.filter(student_class=student_class)

    # Get the selected values for maintaining the form state
    selected_department_id = request.GET.get('department', '')
    selected_class_id = request.GET.get('student_class', '')

    return render(request, 'core/finance_dashboard.html', {
        'form': form,
        'students': students,
        'selected_department_id': selected_department_id,
        'selected_class_id': selected_class_id,
    })


@login_required
@role_required(['registrar'])
def registrar_dashboard(request):
    
    #Registrar dashboard view with options to register a new student.
    
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
   
    #View for displaying all registered students.
    
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
   
    #View for taking attendance with exam time tracking.
    #Generates comprehensive reports including exam status.
    
    students = None
    attended_students = []
    exam_records = {}
    form = AttendanceFilterForm(request.POST or None)
    attendance_type = request.GET.get('attendance_type') or request.session.get('attendance_type')

    if request.method == 'POST':
        if 'filter_students' in request.POST:
            if form.is_valid():
                department = form.cleaned_data['department']
                level = form.cleaned_data['level']
                attendance_type = form.cleaned_data['attendance_type']

                students = Student.objects.all()
                if department:
                    students = students.filter(department=department)
                if level:
                    students = students.filter(student_class=level)

                request.session['attendance_type'] = attendance_type
                request.session['filtered_students'] = list(students.values_list('id', flat=True))

        elif 'end_attendance' in request.POST:
            filtered_student_ids = request.session.get('filtered_students', [])
            students = Student.objects.filter(id__in=filtered_student_ids)
            attendance_type = request.session.get('attendance_type', 'CLASS')
            
            if attendance_type.startswith('EXAM'):
                attended_students = Attendance.objects.filter(
                    student__in=students,
                    teacher=request.user,
                    attendance_type__in=['EXAM_START', 'EXAM_END']
                ).select_related('student')
                
                exam_records = {}
                for student in students:
                    start_record = Attendance.objects.filter(
                        student=student,
                        teacher=request.user,
                        attendance_type='EXAM_START'
                    ).first()
                    
                    end_record = Attendance.objects.filter(
                        student=student,
                        teacher=request.user,
                        attendance_type='EXAM_END'
                    ).first()
                    
                    status = "Not Started"
                    if start_record and end_record:
                        status = "Completed"
                    elif start_record:
                        status = "Started"
                    
                    exam_records[student.id] = {
                        'exam_start_time': start_record.timestamp if start_record else None,
                        'exam_end_time': end_record.timestamp if end_record else None,
                        'status': status
                    }
            else:
                attended_students = Attendance.objects.filter(
                    student__in=students,
                    teacher=request.user,
                    attendance_type=attendance_type
                ).select_related('student')
            
            return generate_attendance_report(
                students, 
                attended_students, 
                request=request, 
                attendance_type=attendance_type,
                exam_records=exam_records if attendance_type.startswith('EXAM') else None
            )

    filtered_student_ids = request.session.get('filtered_students', [])
    attendance_type = request.session.get('attendance_type', 'CLASS')
    
    if filtered_student_ids:
        students = Student.objects.filter(id__in=filtered_student_ids)
        attended_students = Attendance.objects.filter(
            student__in=students,
            teacher=request.user,
            attendance_type=attendance_type
        ).select_related('student')
        
        if attendance_type in ['EXAM_START', 'EXAM_END']:
            exam_records = {}
            for student in students:
                start_record = Attendance.objects.filter(
                    student=student,
                    teacher=request.user,
                    attendance_type='EXAM_START'
                ).first()
                
                end_record = Attendance.objects.filter(
                    student=student,
                    teacher=request.user,
                    attendance_type='EXAM_END'
                ).first()
                
                exam_records[student.id] = {
                    'exam_start_time': start_record.timestamp if start_record else None,
                    'exam_end_time': end_record.timestamp if end_record else None,
                    'has_started': start_record is not None,
                    'has_finished': end_record is not None
                }

    if students and exam_records:
        for student in students:
            student.exam_start_time = exam_records.get(student.id, {}).get('exam_start_time')
            student.exam_end_time = exam_records.get(student.id, {}).get('exam_end_time')
            student.has_started = exam_records.get(student.id, {}).get('has_started', False)
            student.has_finished = exam_records.get(student.id, {}).get('has_finished', False)

    return render(request, 'core/take_attendance.html', {
        'form': form,
        'students': students,
        'attended_students': [a.student for a in attended_students],
        'attendance_type': attendance_type,
        'exam_records': exam_records,
    })
@csrf_exempt
@login_required
@role_required(['teacher'])
def scan_nfc(request):
   
    #Handle NFC card scanning via AJAX.
    
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





@login_required
@role_required(['gatekeeper'])
def scan_card(request):
   
    #View for scanning NFC cards and loading student profiles.
    
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
    
    #Finance dashboard view with filtering functionality.
    
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
   
    #View for finance staff to view and update a student's payment status.
    
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
    
    #View to display all registered students with filtering functionality.
    
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
            student = form.save(commit=False)
            student.nfc_url = student.generate_nfc_url(request)
            student.save()
            messages.success(request, f'Thank you for registering {student.first_name} {student.last_name}!')
            return redirect('registrar-dashboard')
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    field_label = form.fields[field].label if field in form.fields else field
                    messages.error(request, f"{field_label}: {error}")
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'core/register_student.html', {'form': form})

@login_required
@role_required(['registrar'])
def edit_student(request, student_id):
    
    #View to edit a single student's details.
    
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


@login_required
@role_required(['registrar'])
def edit_students(request):
    
    #View to bulk edit students' class.
    
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
    
    #View to delete selected students.
    
    if request.method == 'POST':
        student_ids = request.POST.getlist('selected_students')
        Student.objects.filter(id__in=student_ids).delete()
        messages.success(request, "Selected students deleted successfully.")
        return redirect('registered-students')
    
def get_classes_by_department(request):
    department_id = request.GET.get('department')
    if department_id:
        classes = Class.objects.filter(department_id=department_id).values('id', 'name')
        return JsonResponse(list(classes), safe=False)
    return JsonResponse([], safe=False)



@login_required
@role_required(['teacher'])
def reset_attendance(request):
    
    #View to reset attendance data for the current teacher's session
    
    attendance_type = request.session.get('attendance_type')
    
    if attendance_type:
        # Delete attendance records for this teacher and attendance type
        Attendance.objects.filter(
            teacher=request.user,
            attendance_type=attendance_type
        ).delete()
        
        # Clear filtered students from session
        if 'filtered_students' in request.session:
            del request.session['filtered_students']
        
        messages.success(request, "Attendance data has been reset successfully.")
    else:
        messages.warning(request, "No active attendance session to reset.")
    
    return redirect('take-attendance')

def generate_attendance_report(filtered_students, attended_students, request=None, attendance_type=None, exam_records=None):
    
    #Generate attendance PDF report with consistent styling and proper background coverage
    
    # Get metadata
    teacher_name = "System Generated"
    if request and hasattr(request, 'user'):
        teacher = request.user
        if teacher.is_authenticated:
            full_name = f"{teacher.first_name} {teacher.last_name}".strip()
            teacher_name = full_name if full_name else teacher.username
    
    kigali_tz = pytz.timezone('Africa/Kigali')
    current_time = timezone.now().astimezone(kigali_tz)
    time_str = current_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')
    
    # Get department and class info
    department = "N/A"
    student_class = "N/A"
    if filtered_students.exists():
        first_student = filtered_students.first()
        department = getattr(first_student.department, 'name', 'N/A')
        student_class = getattr(first_student.student_class, 'name', 'N/A')
    
    attended_student_ids = {attendance.student.id for attendance in attended_students}
    display_attendance_type = "Class" if attendance_type and attendance_type.upper() == "CLASS" else "Exam"
    
    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    filename = f"attendance_{display_attendance_type.lower()}_{current_time.strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    margin = 50
    y = height - margin
    
    # Constants for styling
    HEADER_COLOR = colors.HexColor('#3a7bd5')  # Blue
    ROW_COLOR_1 = colors.HexColor('#ffffff')   # White
    ROW_COLOR_2 = colors.HexColor('#f8f9fa')   # Light gray
    WARNING_COLOR = colors.HexColor('#fff3cd')  # Light yellow
    SUCCESS_COLOR = colors.HexColor('#d4edda')  # Light green
    DANGER_COLOR = colors.HexColor('#f8d7da')  # Light red
    
    # Header with full-width background
    p.setFillColor(HEADER_COLOR)
    p.rect(0, y-30, width, 50, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2, y-20, "ATTENDANCE REPORT")
    y -= 60
    
    # Metadata section with consistent spacing
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y, "Report Details:")
    y -= 25
    
    p.setFont("Helvetica", 10)
    details = [
        ("Generated By:", teacher_name),
        ("Report Date:", time_str),
        ("Type:", display_attendance_type),
        ("Department:", department),
        ("Class:", student_class),
        ("Total Students:", str(filtered_students.count())),
        ("Present:", str(len(attended_student_ids))),
        ("Absent:", str(filtered_students.count() - len(attended_student_ids))),
    ]
    
    for label, value in details:
        p.drawString(margin, y, f"{label} {value}")
        y -= 18  # Increased spacing
    
    y -= 25
    
    # Table setup
    if display_attendance_type == "Exam":
        headers = ["ID", "Name", "Start Time", "End Time", "Status"]
        col_widths = [60, 150, 100, 100, 80]
    else:
        headers = ["ID", "Name", "Status"]
        col_widths = [60, 200, 100]
    
    table_width = sum(col_widths) + (len(col_widths)-1)*5
    
    # Table header with full-width background
    p.setFillColor(HEADER_COLOR)
    p.rect(margin, y-20, table_width, 25, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 10)
    
    x_pos = margin
    for header, width in zip(headers, col_widths):
        p.drawString(x_pos+3, y-15, header)
        x_pos += width + 5
    
    y -= 30
    
    # Student rows with proper background coverage
    p.setFont("Helvetica", 9)
    for i, student in enumerate(filtered_students):
        # Alternate row colors
        row_color = ROW_COLOR_2 if i % 2 == 0 else ROW_COLOR_1
        p.setFillColor(row_color)
        p.rect(margin, y-5, table_width, 18, fill=1, stroke=0)
        
        p.setFillColor(colors.black)
        attended = student.id in attended_student_ids
        
        # Draw cells with proper padding
        x_pos = margin
        if display_attendance_type == "Exam":
            record = exam_records.get(student.id, {}) if exam_records else {}
            cells = [
                str(student.student_id),
                f"{student.first_name} {student.last_name}",
                record.get('exam_start_time').strftime('%H:%M:%S') if record and record.get('exam_start_time') else "N/A",
                record.get('exam_end_time').strftime('%H:%M:%S') if record and record.get('exam_end_time') else "N/A",
                record.get('status', 'N/A') if record else "N/A"
            ]
            
            # Status highlighting
            status = cells[-1].lower()
            if status == 'present':
                p.setFillColor(colors.HexColor('#28a745'))
            elif status == 'absent':
                p.setFillColor(colors.HexColor('#dc3545'))
        else:
            cells = [
                str(student.student_id),
                f"{student.first_name} {student.last_name}",
                "Present" if attended else "Absent"
            ]
            
            # Attendance highlighting
            if attended:
                p.setFillColor(colors.HexColor('#28a745'))
            else:
                p.setFillColor(colors.HexColor('#dc3545'))
        
        # Draw all cell content
        for content, width in zip(cells, col_widths):
            p.drawString(x_pos+3, y, str(content))
            x_pos += width + 5
            p.setFillColor(colors.black)  # Reset color after status
        
        y -= 20  # Increased row height
        
        if y < 100:
            p.showPage()
            y = height - margin
            # Re-draw header if new page
            p.setFillColor(HEADER_COLOR)
            p.rect(0, y-30, width, 50, fill=1, stroke=0)
            p.setFillColor(colors.white)
            p.setFont("Helvetica-Bold", 16)
            p.drawCentredString(width/2, y-20, "ATTENDANCE REPORT (CONT.)")
            y -= 60
    
    # Footer
    p.setFont("Helvetica", 8)
    p.drawString(margin, 30, "Generated by Smart Student Management System")
    
    p.save()
    return response

@login_required
@role_required(['finance'])
def generate_payment_report(request):
    #Generate payment PDF report with consistent styling and proper backgrounds
    # Get filters and data
    payment_status = request.GET.get('payment_status', '')
    department_id = request.GET.get('department', '')
    class_id = request.GET.get('student_class', '')
    
    # Start with all students
    students = Student.objects.all().select_related('department', 'student_class')
    
    # Apply filters - modified to properly handle payment status
    if payment_status and payment_status.lower() in ['paid', 'unpaid']:
        students = students.filter(payment_status__iexact=payment_status)
    
    if department_id:
        try:
            department = Department.objects.get(id=department_id)
            students = students.filter(department_id=department_id)
        except Department.DoesNotExist:
            department = None
    
    if class_id:
        try:
            student_class = Class.objects.get(id=class_id)
            students = students.filter(student_class_id=class_id)
        except Class.DoesNotExist:
            student_class = None
    
    # Get filter names for display
    department_name = department.name if department_id and hasattr(locals().get('department', None), 'name') else "All Departments"
    class_name = student_class.name if class_id and hasattr(locals().get('student_class', None), 'name') else "All Classes"
    
    # Metadata
    teacher_name = "System Generated"
    if request and hasattr(request, 'user'):
        teacher = request.user
        if teacher.is_authenticated:
            full_name = f"{teacher.first_name} {teacher.last_name}".strip()
            teacher_name = full_name if full_name else teacher.username
    
    kigali_tz = pytz.timezone('Africa/Kigali')
    current_time = timezone.now().astimezone(kigali_tz)
    time_str = current_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')
    
    # Create PDF
    response = HttpResponse(content_type='application/pdf')
    
    # Generate filename based on filters
    filename_parts = ["payment_report"]
    if payment_status:
        filename_parts.append(payment_status.lower())
    if department_id and hasattr(locals().get('department', None), 'name'):
        filename_parts.append(department.name.replace(' ', '_'))
    if class_id and hasattr(locals().get('student_class', None), 'name'):
        filename_parts.append(student_class.name.replace(' ', '_'))
    filename = "_".join(filename_parts) + ".pdf"
    
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    margin = 50
    y = height - margin
    
    # Style constants
    HEADER_COLOR = colors.HexColor('#3a7bd5')  # Blue
    ROW_COLOR_1 = colors.HexColor('#ffffff')   # White
    ROW_COLOR_2 = colors.HexColor('#f8f9fa')   # Light gray
    WARNING_COLOR = colors.HexColor('#fff3cd')  # Light yellow
    SUCCESS_COLOR = colors.HexColor('#d4edda')  # Light green
    
    # Header with full-width background
    p.setFillColor(HEADER_COLOR)
    p.rect(0, y-30, width, 50, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2, y-20, "PAYMENT REPORT")
    y -= 60
    
    # Metadata section
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y, "Report Details:")
    y -= 25
    
    p.setFont("Helvetica", 10)
    details = [
        ("Generated By:", teacher_name),
        ("Report Date:", time_str),
        ("Payment Status:", payment_status.upper() if payment_status else "All Statuses"),
        ("Department:", department_name),
        ("Class:", class_name),
        ("Total Students:", str(students.count())),
    ]
    
    for label, value in details:
        p.drawString(margin, y, f"{label} {value}")
        y -= 18
    
    y -= 25
    
    # Table setup
    headers = ["ID", "Full Name", "Department", "Class", "Payment Status"]
    col_widths = [50, 125, 120, 110, 100]
    table_width = sum(col_widths) + (len(col_widths)-1)*5
    
    # Table header with full background
    p.setFillColor(HEADER_COLOR)
    p.rect(margin, y-20, table_width, 25, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 10)
    
    x_pos = margin
    for header, width in zip(headers, col_widths):
        p.drawString(x_pos+3, y-15, header)
        x_pos += width + 5
    
    y -= 30
    
    # Student rows with proper backgrounds
    p.setFont("Helvetica", 9)
    for i, student in enumerate(students):
        # Highlight based on payment status
        if student.payment_status.lower() == 'unpaid':
            p.setFillColor(WARNING_COLOR)
        elif student.payment_status.lower() == 'paid':
            p.setFillColor(SUCCESS_COLOR)
        else:
            p.setFillColor(ROW_COLOR_2 if i % 2 == 0 else ROW_COLOR_1)
        
        p.rect(margin, y-5, table_width, 18, fill=1, stroke=0)
        p.setFillColor(colors.black)
        
        # Draw cells
        x_pos = margin
        cells = [
            student.student_id,
            f"{student.first_name} {student.last_name}",
            str(student.department) if student.department else "N/A",
            str(student.student_class) if student.student_class else "N/A",
            student.payment_status.upper()
        ]
        
        for content, width in zip(cells, col_widths):
            p.drawString(x_pos+3, y, str(content))
            x_pos += width + 5
        
        y -= 20
        
        if y < 100:
            p.showPage()
            y = height - margin
            # New page header
            p.setFillColor(HEADER_COLOR)
            p.rect(0, y-30, width, 50, fill=1, stroke=0)
            p.setFillColor(colors.white)
            p.setFont("Helvetica-Bold", 16)
            p.drawCentredString(width/2, y-20, "PAYMENT REPORT (CONT.)")
            y -= 60
    
    # Footer
    p.setFont("Helvetica", 8)
    p.drawString(margin, 30, "Generated by Smart Student Management System")
    
    p.save()
    return response

@login_required
@role_required(['registrar'])
def generate_registered_students_report(request):
    #Generate registered students PDF with proper background coverage
    # Get filters
    campus_id = request.GET.get('campus')
    college_id = request.GET.get('college')
    school_id = request.GET.get('school')
    department_id = request.GET.get('department')
    class_id = request.GET.get('student_class')

    students = Student.objects.all().select_related(
        'campus', 'college', 'school', 'department', 'student_class'
    )
    
    if campus_id:
        students = students.filter(campus_id=campus_id)
        campus = Campus.objects.get(id=campus_id)
    if college_id:
        students = students.filter(college_id=college_id)
        college = College.objects.get(id=college_id)
    if school_id:
        students = students.filter(school_id=school_id)
        school = School.objects.get(id=school_id)
    if department_id:
        students = students.filter(department_id=department_id)
        department = Department.objects.get(id=department_id)
    if class_id:
        students = students.filter(student_class_id=class_id)
        student_class = Class.objects.get(id=class_id)

    # Metadata
    teacher_name = "System Generated"
    if request and hasattr(request, 'user'):
        teacher = request.user
        if teacher.is_authenticated:
            full_name = f"{teacher.first_name} {teacher.last_name}".strip()
            teacher_name = full_name if full_name else teacher.username
    
    kigali_tz = pytz.timezone('Africa/Kigali')
    current_time = timezone.now().astimezone(kigali_tz)
    time_str = current_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')
    
    # Create landscape PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="student_registration.pdf"'
    
    p = canvas.Canvas(response, pagesize=landscape(A4))
    width, height = landscape(A4)
    margin = 50
    y = height - margin
    
    # Style constants
    HEADER_COLOR = colors.HexColor('#3a7bd5')
    ROW_COLOR_1 = colors.HexColor('#ffffff')
    ROW_COLOR_2 = colors.HexColor('#f8f9fa')
    
    # Header with full-width background
    p.setFillColor(HEADER_COLOR)
    p.rect(0, y-30, width, 50, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2, y-20, "STUDENT REGISTRATION REPORT")
    y -= 60
    
    # Metadata section
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y, "Report Details:")
    y -= 25
    
    p.setFont("Helvetica", 10)
    details = [
        ("Generated By:", teacher_name),
        ("Report Date:", time_str),
    ]
    
    if campus_id:
        details.append(("Campus:", campus.name))
    if college_id:
        details.append(("College:", college.name))
    if school_id:
        details.append(("School:", school.name))
    if department_id:
        details.append(("Department:", department.name))
    if class_id:
        details.append(("Class:", student_class.name))
    
    details.append(("Total Students:", str(students.count())))
    
    for label, value in details:
        p.drawString(margin, y, f"{label} {value}")
        y -= 18
    
    y -= 25
    
    # Table setup (landscape optimized)
    headers = ['ID', 'Name', 'Gender', 'Class', 'Department', 'School', 'College', 'Campus']
    col_widths = [60, 120, 50, 100, 110, 80, 80, 80]
    table_width = sum(col_widths) + (len(col_widths)-1)*5
    
    # Table header with full background
    p.setFillColor(HEADER_COLOR)
    p.rect(margin, y-20, table_width, 25, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 10)
    
    x_pos = margin
    for header, width in zip(headers, col_widths):
        p.drawString(x_pos+3, y-15, header)
        x_pos += width + 5
    
    y -= 30
    
    # Student rows with proper backgrounds
    p.setFont("Helvetica", 9)
    
    if students.exists():
        for i, student in enumerate(students):
            # Alternate row colors
            row_color = ROW_COLOR_2 if i % 2 == 0 else ROW_COLOR_1
            p.setFillColor(row_color)
            p.rect(margin, y-5, table_width, 18, fill=1, stroke=0)
            p.setFillColor(colors.black)
            
            # Draw cells
            x_pos = margin
            cells = [
                student.student_id,
                f"{student.first_name} {student.last_name}",
                student.gender,
                str(student.student_class),
                str(student.department),
                str(student.school),
                str(student.college),
                str(student.campus),
            ]
            
            for content, width in zip(cells, col_widths):
                p.drawString(x_pos+3, y, str(content))
                x_pos += width + 5
            
            y -= 20
            
            if y < 100:
                p.showPage()
                y = height - margin
                # New page header
                p.setFillColor(HEADER_COLOR)
                p.rect(0, y-30, width, 50, fill=1, stroke=0)
                p.setFillColor(colors.white)
                p.setFont("Helvetica-Bold", 16)
                p.drawCentredString(width/2, y-20, "STUDENT REGISTRATION (CONT.)")
                y -= 60
    else:
        # No results message
        p.setFillColor(ROW_COLOR_2)
        p.rect(margin, y-5, table_width, 18, fill=1, stroke=0)
        p.setFillColor(colors.black)
        p.drawCentredString(width/2, y, "No students found matching the criteria")
        y -= 20
    
    # Footer
    p.setFont("Helvetica", 8)
    p.drawString(margin, 30, "Generated by Smart Student Management System")
    
    p.save()
    return response
@login_required
@role_required(['gatekeeper'])
def export_entries(request):
    
    #Generate student entries/exits PDF report with consistent styling
    
    # Get filter parameters
    date_str = request.GET.get('date', '')
    department_id = request.GET.get('department', '')
    class_id = request.GET.get('class', '')
    
    # Date handling
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
    except ValueError:
        selected_date = timezone.now().date()
    
    # Timezone-aware date filtering
    timezone_aware_date = timezone.make_aware(
        datetime.combine(selected_date, datetime.min.time())
    )
    next_day = timezone_aware_date + timezone.timedelta(days=1)
    
    # Base query
    entries = StudentEntry.objects.filter(
        entry_time__gte=timezone_aware_date,
        entry_time__lt=next_day
    ).select_related('student', 'student__department', 'student__student_class').order_by('entry_time')
    
    # Apply filters
    if department_id:
        entries = entries.filter(student__department_id=department_id)
        department = Department.objects.get(id=department_id)
    if class_id:
        entries = entries.filter(student__student_class_id=class_id)
        student_class = Class.objects.get(id=class_id)
    
    # Get teacher name
    teacher_name = "System Generated"
    if request and hasattr(request, 'user'):
        teacher = request.user
        if teacher.is_authenticated:
            full_name = f"{teacher.first_name} {teacher.last_name}".strip()
            teacher_name = full_name if full_name else teacher.username
    
    # Get current time
    kigali_tz = pytz.timezone('Africa/Kigali')
    current_time = timezone.now().astimezone(kigali_tz)
    time_str = current_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')
    
    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    filename = f"student_entries_{selected_date.strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    p = canvas.Canvas(response, pagesize=landscape(A4))
    width, height = landscape(A4)
    margin = 50
    y = height - margin
    
    # Style constants
    HEADER_COLOR = colors.HexColor('#3a7bd5')  # Blue
    ROW_COLOR_1 = colors.HexColor('#ffffff')   # White
    ROW_COLOR_2 = colors.HexColor('#f8f9fa')   # Light gray
    ACTIVE_COLOR = colors.HexColor('#d4edda')  # Light green for active entries
    
    # Header with full-width background
    p.setFillColor(HEADER_COLOR)
    p.rect(0, y-30, width, 50, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2, y-20, "STUDENT ENTRIES REPORT")
    y -= 60
    
    # Metadata section
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y, "Report Details:")
    y -= 25
    
    p.setFont("Helvetica", 10)
    details = [
        ("Generated By:", teacher_name),
        ("Report Date:", time_str),
        ("Entries Date:", selected_date.strftime('%Y-%m-%d')),
    ]
    
    if department_id:
        details.append(("Department:", department.name))
    if class_id:
        details.append(("Class:", student_class.name))
    
    details.extend([
        ("Total Entries:", str(entries.count())),
        ("Currently in School:", str(entries.filter(exit_time__isnull=True).count()))
    ])
    
    for label, value in details:
        p.drawString(margin, y, f"{label} {value}")
        y -= 18
    
    y -= 25
    
    # Table setup
    headers = ['Student ID', 'Name', 'Department', 'Class', 'Entry Time', 'Exit Time', 'Duration']
    col_widths = [80, 150, 120, 100, 100, 100, 80]
    table_width = sum(col_widths) + (len(col_widths)-1)*5
    
    # Table header with full background
    p.setFillColor(HEADER_COLOR)
    p.rect(margin, y-20, table_width, 25, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 10)
    
    x_pos = margin
    for header, width in zip(headers, col_widths):
        p.drawString(x_pos+3, y-15, header)
        x_pos += width + 5
    
    y -= 30
    
    # Entry rows with proper backgrounds
    p.setFont("Helvetica", 9)
    for i, entry in enumerate(entries):
        # Highlight active entries (no exit time)
        if entry.exit_time is None:
            p.setFillColor(ACTIVE_COLOR)
        else:
            p.setFillColor(ROW_COLOR_2 if i % 2 == 0 else ROW_COLOR_1)
        
        p.rect(margin, y-5, table_width, 18, fill=1, stroke=0)
        p.setFillColor(colors.black)
        
        # Calculate duration if exited
        duration = ""
        if entry.exit_time:
            delta = entry.exit_time - entry.entry_time
            total_seconds = delta.total_seconds()
            minutes = int(total_seconds // 60)
            duration = f"{minutes} mins"
        
        # Draw cells
        x_pos = margin
        cells = [
            entry.student.student_id,
            f"{entry.student.first_name} {entry.student.last_name}",
            entry.student.department.name if entry.student.department else "N/A",
            entry.student.student_class.name if entry.student.student_class else "N/A",
            entry.entry_time.time().strftime("%H:%M:%S"),
            entry.exit_time.time().strftime("%H:%M:%S") if entry.exit_time else "ACTIVE",
            duration
        ]
        
        for content, width in zip(cells, col_widths):
            p.drawString(x_pos+3, y, str(content))
            x_pos += width + 5
        
        y -= 20
        
        if y < 100:
            p.showPage()
            y = height - margin
            # New page header
            p.setFillColor(HEADER_COLOR)
            p.rect(0, y-30, width, 50, fill=1, stroke=0)
            p.setFillColor(colors.white)
            p.setFont("Helvetica-Bold", 16)
            p.drawCentredString(width/2, y-20, "STUDENT ENTRIES REPORT (CONT.)")
            y -= 60
    
    # Footer
    p.setFont("Helvetica", 8)
    p.drawString(margin, 30, "Generated by Smart Student Management System")
    
    p.save()
    return response


def get_system_statistics(request):
    """Return system statistics for the landing page"""
    stats = {
        'total_students': Student.objects.count(),
        'campuses': list(Campus.objects.annotate(
            student_count=Count('students')
        ).values('name', 'student_count')),
        'colleges': list(College.objects.annotate(
            student_count=Count('students')
        ).values('name', 'student_count')),
        'schools': list(School.objects.annotate(
            student_count=Count('students')
        ).order_by('-student_count')[:5].values('name', 'student_count')),
        'departments': list(Department.objects.annotate(
            student_count=Count('students')
        ).order_by('-student_count')[:5].values('name', 'student_count')),
        'latest_registered': list(Student.objects.order_by('-id')[:5].values(
            'student_id', 'first_name', 'last_name'
        ))
    }
    return JsonResponse(stats)


@login_required
@role_required(['gatekeeper'])
def student_search_api(request):
    term = request.GET.get('term', '')
    students = Student.objects.filter(
        Q(student_id__icontains=term) |
        Q(first_name__icontains=term) |
        Q(last_name__icontains=term)
    ).values('student_id', 'first_name', 'last_name')[:10]
    
    results = []
    for student in students:
        results.append({
            'value': student['student_id'],
            'label': f"{student['first_name']} {student['last_name']}"
        })
    
    return JsonResponse(results, safe=False)
## filepath: core/views.py

from django.shortcuts import render, get_object_or_404 , redirect 
from .models import Student
from accounts.decorators import role_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import StudentRegistrationForm

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
@role_required('gatekeeper')
def gatekeeper_dashboard(request):
    return render(request, 'core/gatekeeper_dashboard.html')

@login_required
@role_required('teacher')
def teacher_dashboard(request):
    return HttpResponse("core/teacher_dashboard.html")

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
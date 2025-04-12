## filepath: core/views.py

from django.shortcuts import render, get_object_or_404
from .models import Student
from accounts.decorators import role_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

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

@login_required
@role_required('registrar')
def registrar_dashboard(request):
    return HttpResponse("core/registar_dashboard.html")

@login_required
@role_required('finance')
def finance_dashboard(request):
    return HttpResponse("core/finance_dashboard.html")
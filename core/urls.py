# filepath: core/urls.py

from django.urls import path
from . import views



urlpatterns = [
    path('profile/<str:student_id>/', views.student_profile, name='student-profile'),
    path('gatekeeper/dashboard/', views.gatekeeper_dashboard, name='gatekeeper-dashboard'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher-dashboard'),
    path('registrar/dashboard/', views.registrar_dashboard, name='registrar-dashboard'),
    path('finance/dashboard/', views.finance_dashboard, name='finance-dashboard'),
    path('registrar/register-student/', views.register_student, name='register-student'),
    path('students/', views.view_all_students, name='view-all-students'),
    path('teacher/take-attendance/', views.take_attendance, name='take-attendance'),
    path('ajax/load-colleges/', views.load_colleges, name='ajax_load_colleges'),
    path('ajax/load-schools/', views.load_schools, name='ajax_load_schools'),
    path('ajax/load-departments/', views.load_departments, name='ajax_load_departments'),
    path('ajax/load-classes/', views.load_classes, name='ajax_load_classes'),
]
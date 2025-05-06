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
    path('gatekeeper/scan-card/', views.scan_card, name='scan-card'),
    path('finance/dashboard/', views.finance_dashboard, name='finance-dashboard'),
    path('finance/student/<int:student_id>/', views.finance_student_detail, name='finance-student-detail'),
    path('registrar/registered-students/', views.registered_students, name='registered-students'),
    path('registrar/register-student/', views.register_student, name='register-student'),
    path('student/<str:student_id>/', views.student_profile, name='student-profile'),
    path('teacher/scan-nfc/', views.scan_nfc, name='scan-nfc'),
    path('registrar/edit-student/<int:student_id>/', views.edit_student, name='edit-student'),
    path('registrar/edit-students/', views.edit_students, name='edit-students'),
    path('registrar/delete-students/', views.delete_students, name='delete-students'),
    path('gatekeeper/export-entries/', views.export_entries, name='export-entries'),
    path('api/classes/', views.get_classes_by_department, name='get_classes_by_department'),
    path('ajax/load-classes/', views.load_classes, name='load_classes'),
    path('teacher/reset-attendance/', views.reset_attendance, name='reset-attendance'),
    path('finance/report/', views.generate_payment_report, name='generate-payment-report'),
    path('registrar/report/', views.generate_registered_students_report, name='registrar-report'), 
    path('api/statistics/', views.get_system_statistics, name='system-statistics'),  
]
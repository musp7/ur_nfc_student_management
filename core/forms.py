from django import forms
from .models import Student
from .models import Attendance, Department, Class

class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'  # Include all fields from the Student model

class AttendanceFilterForm(forms.Form):
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),  # Use the Department model
        required=False,
        label="Department"
    )
    level = forms.ModelChoiceField(
        queryset=Class.objects.all(),  # Use the Class model
        required=False,
        label="Level"
    )
    attendance_type = forms.ChoiceField(
        choices=Attendance.ATTENDANCE_TYPE_CHOICES,
        required=True,
        label="Attendance Type"
    )

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'attendance_type']    
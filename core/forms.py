from django import forms
from .models import Student, Attendance,Campus, College, School, Department, Class



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

class PaymentStatusForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['payment_status']   

class FinanceFilterForm(forms.Form):
    payment_status = forms.ChoiceField(
        choices=[('', 'All')] + Student.PAYMENT_STATUS_CHOICES,
        required=False,
        label="Payment Status"
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label="Department"
    )
    student_class = forms.ModelChoiceField(
        queryset=Class.objects.all(),
        required=False,
        label="Class"
    )

class RegistrarFilterForm(forms.Form):
    campus = forms.ModelChoiceField(
        queryset=Campus.objects.all(),
        required=False,
        label="Campus"
    )
    college = forms.ModelChoiceField(
        queryset=College.objects.all(),
        required=False,
        label="College"
    )
    school = forms.ModelChoiceField(
        queryset=School.objects.all(),
        required=False,
        label="School"
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label="Department"
    )
    student_class = forms.ModelChoiceField(
        queryset=Class.objects.all(),
        required=False,
        label="Class"
    )
from django import forms
from .models import Student
from .models import Attendance


from .models import Campus, College, School, Department, Class


# class StudentRegistrationForm(forms.ModelForm):
#     class Meta:
#         model = Student
#         fields = [
#             'student_id', 'first_name', 'last_name', 'gender', 'payment_status',
#             'campus', 'college', 'school', 'department', 'student_class', 'photo', 'nfc_url'
#         ]
#         widgets = {
#             'gender': forms.Select(choices=[('Male', 'Male'), ('Female', 'Female')]),
#             'payment_status': forms.Select(choices=[('PAID', 'Paid'), ('UNPAID', 'Unpaid'), ('PENDING', 'Pending')]),
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['college'].queryset = College.objects.none()
#         self.fields['school'].queryset = School.objects.none()
#         self.fields['department'].queryset = Department.objects.none()
#         self.fields['student_class'].queryset = Class.objects.none()

#         if 'campus' in self.data:
#             try:
#                 campus_id = int(self.data.get('campus'))
#                 self.fields['college'].queryset = College.objects.filter(campus_id=campus_id)
#             except (ValueError, TypeError):
#                 pass

#         if 'college' in self.data:
#             try:
#                 college_id = int(self.data.get('college'))
#                 self.fields['school'].queryset = School.objects.filter(college_id=college_id)
#             except (ValueError, TypeError):
#                 pass

#         if 'school' in self.data:
#             try:
#                 school_id = int(self.data.get('school'))
#                 self.fields['department'].queryset = Department.objects.filter(school_id=school_id)
#             except (ValueError, TypeError):
#                 pass

#         if 'department' in self.data:
#             try:
#                 department_id = int(self.data.get('department'))
#                 self.fields['student_class'].queryset = Class.objects.filter(department_id=department_id)
#             except (ValueError, TypeError):
#                 pass

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
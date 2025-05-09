from django import forms
from .models import Student, Attendance,Campus, College, School, Department, Class



class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'  # or specify all your fields explicitly
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Safely set required fields only if they exist
        if 'campus' in self.fields:
            self.fields['campus'].required = True
            self.fields['campus'].widget.attrs.update({'class': 'form-select'})
            
        # Check if the field is named 'class' or something else
        class_field_name = 'class' if 'class' in self.fields else 'student_class'
        if class_field_name in self.fields:
            self.fields[class_field_name].required = True
            self.fields[class_field_name].widget.attrs.update({'class': 'form-select'})
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Check campus
        if 'campus' in self.fields and not cleaned_data.get('campus'):
            self.add_error('campus', 'Please select a campus')
            
        # Check class (using the correct field name)
        class_field_name = 'class' if 'class' in self.fields else 'student_class'
        if class_field_name in self.fields and not cleaned_data.get(class_field_name):
            self.add_error(class_field_name, 'Please select a class')
        
        return cleaned_data

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
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label="Department"
    )
    school = forms.ModelChoiceField(
        queryset=School.objects.all(),
        required=False,
        label="School"
    )
    
    student_class = forms.ModelChoiceField(
        queryset=Class.objects.all(),
        required=False,
        label="Class"
    )

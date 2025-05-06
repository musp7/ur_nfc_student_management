from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils.timezone import now

from accounts.models import CustomUser


class Campus(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "Campuses"


class College(models.Model):
    name = models.CharField(max_length=100)
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name='colleges')

    class Meta:
        unique_together = ('name', 'campus')  # Ensure unique colleges within a campus

    def __str__(self):
        return f"{self.name} ({self.campus.name})"


class School(models.Model):
    name = models.CharField(max_length=100)
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='schools')

    class Meta:
        unique_together = ('name', 'college')  # Ensure unique schools within a college

    def __str__(self):
        return f"{self.name} ({self.college.name})"


class Department(models.Model):
    name = models.CharField(max_length=100)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='departments')

    class Meta:
        unique_together = ('name', 'school')  # Ensure unique departments within a school

    def __str__(self):
        return f"{self.name} ({self.school.name})"


class Class(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='classes')

    class Meta:
        verbose_name_plural = "Classes"
        unique_together = ('name', 'department')  # Ensure unique classes within a department

    def __str__(self):
        return f"{self.name} ({self.department.name})"





class Student(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PAID', 'Paid'),
        ('UNPAID', 'Unpaid'),
        ('PENDING', 'Pending'),
    ]

    student_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        default='Male'
    )
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING'
    )
    campus = models.ForeignKey(
        'Campus',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    college = models.ForeignKey(
        'College',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    school = models.ForeignKey(
        'School',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    student_class = models.ForeignKey(
        'Class',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    
    LAPTOP_MODEL_CHOICES = [
        ('HP', 'HP'),
        ('Dell', 'Dell'),
        ('Lenovo', 'Lenovo'),
        ('MacBook', 'MacBook'),
        ('Acer', 'Acer'),
        ('Asus', 'Asus'),
        ('Other', 'Other'),
    ]
    
    laptop_model = models.CharField(
        max_length=20,
        choices=LAPTOP_MODEL_CHOICES,
        blank=True,
        null=True,
        verbose_name="Laptop Model"
    )
    laptop_serial = models.CharField(max_length=50, blank=True, null=True)
    photo = models.ImageField(
        upload_to='student_photos/',
        blank=True,
        null=True
    )
    nfc_url = models.URLField(
        blank=True,
        null=True
    )
    def generate_nfc_url(self, request):
        """
        Generate the full NFC URL dynamically based on the request's host.
        Includes the current attendance type if available.
        """
        scheme = request.scheme  # 'http' or 'https'
        host = request.get_host()  # e.g., '127.0.0.1:8000' or 'example.com'
        base_url = f"{scheme}://{host}{reverse('student-profile', args=[self.student_id])}"
        
        # Get attendance type from session if available
        attendance_type = request.session.get('attendance_type')
        if attendance_type:
            return f"{base_url}?attendance_type={attendance_type}"
        return base_url

    def save(self, *args, **kwargs):
        # If `request` is passed in kwargs, use it to generate the NFC URL
        request = kwargs.pop('request', None)
        if request and not self.nfc_url:
            self.nfc_url = self.generate_nfc_url(request)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"
    def get_exam_status(self, teacher):
        """
        Returns the exam status for this student with the given teacher.
        """
        start_record = Attendance.objects.filter(
            student=self,
            teacher=teacher,
            attendance_type='EXAM_START'
        ).first()
        
        end_record = Attendance.objects.filter(
            student=self,
            teacher=teacher,
            attendance_type='EXAM_END'
        ).first()
        
        if not start_record:
            return "Not started"
        elif start_record and not end_record:
            return f"Started at {start_record.timestamp.time()}"
        else:
            return f"Submitted at {end_record.timestamp.time()}"
    


class Attendance(models.Model):
    ATTENDANCE_TYPE_CHOICES = [
        ('CLASS', 'Class'),
        ('EXAM_START', 'Exam Start'),
        ('EXAM_END', 'Exam End'),
    ]

    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    teacher = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    attendance_type = models.CharField(max_length=20, choices=ATTENDANCE_TYPE_CHOICES)
    timestamp = models.DateTimeField(default=now)

    class Meta:
        unique_together = ('student', 'teacher', 'attendance_type')  # Prevent duplicate records

    def __str__(self):
        return f"{self.student} - {self.attendance_type} - {self.timestamp}"
    
# core/models.py
from django.utils import timezone

class StudentEntry(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    gatekeeper = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name_plural = "Student Entries"
        ordering = ['-entry_time']
        
    def __str__(self):
        return f"{self.student} - {self.entry_time}"
    


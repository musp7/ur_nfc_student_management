from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils.timezone import now


class Campus(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


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
        unique_together = ('name', 'department')  # Ensure unique classes within a department

    def __str__(self):
        return f"{self.name} ({self.department.name})"

# class Campus(models.Model):
#     name = models.CharField(max_length=100, unique=True)

#     def __str__(self):
#         return self.name


# class College(models.Model):
#     name = models.CharField(max_length=100, unique=True)
#     campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="colleges")

#     def __str__(self):
#         return f"{self.name} ({self.campus.name})"


# class School(models.Model):
#     name = models.CharField(max_length=100, unique=True)
#     college = models.ForeignKey(College, on_delete=models.CASCADE, related_name="schools")

#     def __str__(self):
#         return f"{self.name} ({self.college.name})"


# class Department(models.Model):
#     name = models.CharField(max_length=100, unique=True)
#     school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="departments")

#     def __str__(self):
#         return f"{self.name} ({self.school.name})"


# class Class(models.Model):
#     name = models.CharField(max_length=100, unique=True)
#     department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="classes")

#     def __str__(self):
#         return f"{self.name} ({self.department.name})"


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
        """
        scheme = request.scheme  # 'http' or 'https'
        host = request.get_host()  # e.g., '127.0.0.1:8000' or 'example.com'
        return f"{scheme}://{host}{reverse('student-profile', args=[self.student_id])}"

    def save(self, *args, **kwargs):
        # If `request` is passed in kwargs, use it to generate the NFC URL
        request = kwargs.pop('request', None)
        if request and not self.nfc_url:
            self.nfc_url = self.generate_nfc_url(request)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"
    
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

    def __str__(self):
        return f"{self.student} - {self.attendance_type} - {self.timestamp}"


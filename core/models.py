from django.db import models
from django.urls import reverse
from django.conf import settings

class Campus(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class College(models.Model):
    name = models.CharField(max_length=100, unique=True)
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="colleges")

    def __str__(self):
        return f"{self.name} ({self.campus.name})"


class School(models.Model):
    name = models.CharField(max_length=100, unique=True)
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name="schools")

    def __str__(self):
        return f"{self.name} ({self.college.name})"


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="departments")

    def __str__(self):
        return f"{self.name} ({self.school.name})"


class Class(models.Model):
    name = models.CharField(max_length=100, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="classes")

    def __str__(self):
        return f"{self.name} ({self.department.name})"


class Student(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('PAID', 'Paid'),
        ('UNPAID', 'Unpaid'),
        ('PENDING', 'Pending'),
    ]
    student_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING'
    )
    campus = models.ForeignKey('Campus', on_delete=models.SET_NULL, null=True, blank=True)
    college = models.ForeignKey('College', on_delete=models.SET_NULL, null=True, blank=True)
    school = models.ForeignKey('School', on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
    student_class = models.ForeignKey('Class', on_delete=models.SET_NULL, null=True, blank=True)
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    nfc_url = models.URLField(blank=True, null=True)
 

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
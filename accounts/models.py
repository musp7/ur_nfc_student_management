from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('gatekeeper', 'Gatekeeper'),
        ('teacher', 'Teacher'),
        ('registrar', 'Registrar'),
        ('finance', 'Finance'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='gatekeeper')

    def __str__(self):
        return f"{self.username} ({self.role})"
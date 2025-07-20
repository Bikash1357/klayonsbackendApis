# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
import random
import string
from datetime import datetime, timedelta
from django.utils import timezone

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    society_name = models.CharField(max_length=100, blank=True, null=True)
    flat_no = models.CharField(max_length=20, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    purpose = models.CharField(max_length=20, choices=[
        ('registration', 'Registration'),
        ('login', 'Login'),
    ])

    def generate_otp(self):
        self.otp_code = ''.join(random.choices(string.digits, k=6))
        return self.otp_code

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)


    class Meta:
        ordering = ['-created_at']

from django.contrib.auth.models import AbstractUser
from django.db import models
from v1.models import Company

# Create your models here.


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('store_admin', 'Store Admin'),
        ('pos_staff', 'POS Staff'),
    ]
    phone_number = models.CharField(max_length=15, unique=True)
    verified = models.BooleanField(default=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    plain_password = models.CharField(max_length=128, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True, blank=True)

    def __str__(self):
        return self.username
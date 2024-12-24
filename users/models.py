from django.contrib.auth.models import AbstractUser
from django.db import models
from v1.models import Company

# Create your models here.


class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True)
    verified = models.BooleanField(default=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    plain_password = models.CharField(max_length=128, null=True, blank=True)

    def __str__(self):
        return self.username
from django.db import models

from v1.models import Outlet  # Assuming Outlet model is in the app named 'v1'
from users.models import CustomUser  # Assuming your custom User model is in the 'users' app

# Create your models here.

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('CLOSED', 'Closed'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE)
    raised_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='raised_tickets')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
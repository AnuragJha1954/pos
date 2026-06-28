from django.db import models
from v1.models import Plan
from users.models import CustomUser

class SubscriptionTransaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed')
    ]
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    
    razorpay_order_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount in INR")
    
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, help_text="Linked to user after signup/login")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.email or self.phone_number} - {self.plan.plan_name if self.plan else 'Unknown'} - {self.status}"

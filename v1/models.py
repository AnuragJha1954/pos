from django.db import models
from django.contrib.auth import get_user_model
from datetime import date
from django.conf import settings
# Create your models here.


class Company(models.Model):
    name = models.CharField(max_length=255)
    number_of_outlets = models.IntegerField( null=True, blank=True)
    number_of_employees = models.IntegerField( null=True, blank=True)
    address = models.TextField( null=True, blank=True)
    gst_in = models.CharField(max_length=15, unique=True, null=True, blank=True)
    
    # Add other company details fields here

    def __str__(self):
        return self.name
    
    



class Outlet(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='outlets')
    logo = models.ImageField(upload_to='logos/')
    gst_number = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    account_details = models.TextField()
    outlet_name = models.CharField(max_length=255)
    address = models.TextField()

    def __str__(self):
        return self.outlet_name



class OutletAccess(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE)
    permissions = models.JSONField()

    def __str__(self):
        return f'{self.user} - {self.outlet}'









class Plan(models.Model):
    PLAN_TENURE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually')
    ]

    plan_name = models.CharField(max_length=100)
    plan_price = models.DecimalField(max_digits=10, decimal_places=2)
    price_tenure = models.CharField(max_length=20, choices=PLAN_TENURE_CHOICES)

    def __str__(self):
        return f"{self.plan_name} - {self.price_tenure}"

    class Meta:
        verbose_name = 'Plan'
        verbose_name_plural = 'Plans'






class PlanAssignment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired'),
    ]

    plan = models.ForeignKey('Plan', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    valid_till = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"{self.user} - {self.plan} - {self.status}"

    class Meta:
        verbose_name = 'Plan Assignment'
        verbose_name_plural = 'Plan Assignments'


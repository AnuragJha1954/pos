from django.db import models

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
from django.db import models

# Create your models here.
class OTPDetails(models.Model):
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6, null=True,blank=True)  # Assuming OTP is a 6-digit code

    def __str__(self):
        return f"{self.email} - {self.otp}"
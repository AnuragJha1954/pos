from django.db import models
from v1.models import Outlet
# Create your models here.
class QRCustomization(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='qr_customization')
    qr_tagline = models.CharField(max_length=255, blank=True, null=True)
    qr_logo = models.ImageField(upload_to='qr_logos/', blank=True, null=True)
    theme_color = models.CharField(max_length=7, blank=True, null=True)  # Hex code for theme color (e.g., #FFFFFF)
    # background_color = models.CharField(max_length=7, blank=True, null=True)  # Hex code for background color
    # font_color = models.CharField(max_length=7, blank=True, null=True)  # Hex code for font color
    # button_color = models.CharField(max_length=7, blank=True, null=True)  # Hex code for button color
    # button_text_color = models.CharField(max_length=7, blank=True, null=True)  # Hex code for button text color
    # border_radius = models.IntegerField(default=5)  # To define the roundness of elements (e.g., buttons, cards)
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"QR Customization for {self.outlet.outlet_name}"
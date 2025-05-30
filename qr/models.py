from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.files.base import ContentFile
import qrcode
from io import BytesIO
from v1.models import Outlet, Product
# Create your models here.
class QRCustomization(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='qr_customization')
    qr_tagline = models.CharField(max_length=255, blank=True, null=True)
    qr_logo = models.ImageField(upload_to='qr_logos/', blank=True, null=True)
    theme_color = models.CharField(max_length=7, blank=True, null=True)  # Hex code for theme color (e.g., #FFFFFF)
    color_palette = models.JSONField(blank=True, null=True)  # List of hex codes
    # background_color = models.CharField(max_length=7, blank=True, null=True)  # Hex code for background color
    # font_color = models.CharField(max_length=7, blank=True, null=True)  # Hex code for font color
    # button_color = models.CharField(max_length=7, blank=True, null=True)  # Hex code for button color
    # button_text_color = models.CharField(max_length=7, blank=True, null=True)  # Hex code for button text color
    # border_radius = models.IntegerField(default=5)  # To define the roundness of elements (e.g., buttons, cards)
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"QR Customization for {self.outlet.outlet_name}"





class SpecialMenu(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='special_menus')
    name = models.CharField(max_length=255, default="Special Menu")
    products = models.ManyToManyField(Product, related_name='special_menus')

    def clean(self):
        if self.pk and self.products.count() > 5:
            raise ValidationError("A Special Menu can contain a maximum of 5 products.")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.clean()

    def __str__(self):
        return f"{self.name} ({self.outlet.outlet_name})"




class AdvertisementBanner(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='advertisement_banners')
    image_url = models.URLField(help_text="URL of the banner image.")
    redirect_url = models.URLField(help_text="URL to redirect when the banner is clicked.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Banner for {self.outlet.outlet_name}"




class OutletTableConfiguration(models.Model):
    outlet = models.OneToOneField(Outlet, on_delete=models.CASCADE, related_name='table_config')
    number_of_tables = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.number_of_tables > 0:
            for i in range(1, self.number_of_tables + 1):
                TableQR.objects.get_or_create(
                    outlet=self.outlet,
                    table_number=i
                )
        else:
            TableQR.objects.get_or_create(
                outlet=self.outlet,
                table_number=None
            )

    def __str__(self):
        return f"{self.outlet.outlet_name} - Tables: {self.number_of_tables}"







class TableQR(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='table_qrs')
    table_number = models.PositiveIntegerField(null=True, blank=True)
    qr_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('outlet', 'table_number')

    def save(self, *args, **kwargs):
        if self.table_number:
            qr_url = f"https://qr.mantrapos.com/{self.outlet.id}/{self.table_number}"
        else:
            qr_url = f"https://qr.mantrapos.com/{self.outlet.id}/"

        qr = qrcode.make(qr_url)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        filename = f'qr_{self.outlet.id}_{self.table_number or "outlet"}.png'
        filebuffer = ContentFile(buffer.getvalue())
        self.qr_image.save(filename, filebuffer, save=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"QR for {self.outlet.outlet_name} - Table {self.table_number or 'Outlet'}"


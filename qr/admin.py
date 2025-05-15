from django.contrib import admin
from .models import QRCustomization

@admin.register(QRCustomization)
class QRCustomizationAdmin(admin.ModelAdmin):
    list_display = ('outlet', 'qr_tagline', 'theme_color')
    search_fields = ('outlet__outlet_name', 'qr_tagline')
    list_filter = ('theme_color',)
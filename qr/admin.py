from django.contrib import admin
from .models import QRCustomization, SpecialMenu, AdvertisementBanner, OutletTableConfiguration, TableQR


@admin.register(QRCustomization)
class QRCustomizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'outlet', 'qr_tagline', 'theme_color')
    search_fields = ('outlet__outlet_name', 'qr_tagline', 'theme_color')
    list_filter = ('theme_color',)
    readonly_fields = ('qr_logo',)


@admin.register(SpecialMenu)
class SpecialMenuAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'outlet')
    search_fields = ('name', 'outlet__outlet_name')
    filter_horizontal = ('products',)
    list_filter = ('outlet',)


@admin.register(AdvertisementBanner)
class AdvertisementBannerAdmin(admin.ModelAdmin):
    list_display = ('id', 'outlet', 'image_url', 'redirect_url', 'created_at')
    search_fields = ('outlet__outlet_name', 'image_url', 'redirect_url')
    list_filter = ('created_at',)

@admin.register(OutletTableConfiguration)
class OutletTableConfigurationAdmin(admin.ModelAdmin):
    list_display = ['outlet', 'number_of_tables']

@admin.register(TableQR)
class TableQRAdmin(admin.ModelAdmin):
    list_display = ['outlet', 'table_number', 'qr_image']

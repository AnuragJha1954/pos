from django.contrib import admin
from .models import Company
# Register your models here.


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'number_of_outlets', 'gst_in','number_of_employees')
    search_fields = ('name', 'gst_in')
    list_filter = ('number_of_outlets','number_of_employees',)

    def address_display(self, obj):
        return obj.address
    address_display.short_description = 'Address'
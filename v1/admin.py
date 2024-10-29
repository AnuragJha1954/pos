from django.contrib import admin
from .models import (
    Company,
    Outlet,
    OutletAccess,
    Plan,
    PlanAssignment
    )
# Register your models here.
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'number_of_outlets', 'gst_in','number_of_employees')
    search_fields = ('name', 'gst_in')
    list_filter = ('number_of_outlets','number_of_employees',)

    def address_display(self, obj):
        return obj.address
    address_display.short_description = 'Address'
    
    



@admin.register(Outlet)
class OutletAdmin(admin.ModelAdmin):
    list_display = ('outlet_name', 'company', 'gst_number', 'name')
    search_fields = ('outlet_name', 'company__name', 'gst_number', 'name')
    list_filter = ('company',)
    readonly_fields = ('gst_number',)
    fieldsets = (
        (None, {
            'fields': ('company', 'logo', 'outlet_name', 'gst_number', 'name', 'account_details', 'address')
        }),
    )

@admin.register(OutletAccess)
class OutletAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'outlet', 'permissions')
    search_fields = ('user__username', 'outlet__outlet_name')
    list_filter = ('outlet', 'user')
    fieldsets = (
        (None, {
            'fields': ('user', 'outlet', 'permissions')
        }),
    )
    



@admin.register(Plan)
class PlanAccessAdmin(admin.ModelAdmin):
    list_display = ('plan_name', 'plan_price', 'price_tenure')
    search_fields = ('plan_name',)
    list_filter = ('plan_name',)
    fieldsets = (
        (None, {
            'fields': ('plan_name', 'plan_price', 'price_tenure')
        }),
    )





@admin.register(PlanAssignment)
class PlanAssignmentAccessAdmin(admin.ModelAdmin):
    list_display = ('plan', 'status', 'valid_till','user')
    search_fields = ('plan__plan_name','user__username')
    list_filter = ('status','plan')
    fieldsets = (
        (None, {
            'fields': ('plan', 'status', 'valid_till','user')
        }),
    )


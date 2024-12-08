from django.contrib import admin
from .models import (
    Company,
    Outlet,
    OutletAccess,
    Plan,
    PlanAssignment,
    Employee,
    Product,
    ProductVariant,
    Menu,
    Category,
    Order,
    OrderItem,
    Customer,
    StockRequest
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
    list_display = ('outlet_name', 'company', 'gst_number', 'phone_number', 'is_active', 'created_at')
    search_fields = ('outlet_name', 'company__name', 'gst_number', 'phone_number')
    list_filter = ('company', 'is_active')
    readonly_fields = ('gst_number', 'created_at', 'updated_at')  # Make non-editable fields readonly
    
    fieldsets = (
        (None, {
            'fields': ('company', 'logo', 'gst_number', 'outlet_name', 'phone_number', 'opening_hours', 'is_active', 'bank_account_number', 'ifsc_code', 'address')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),  # Optional: makes the section collapsible
        }),
    )




@admin.register(OutletAccess)
class OutletAccessAdmin(admin.ModelAdmin):
    list_display = ('employee', 'outlet', 'permissions')
    search_fields = ('employee__first_name', 'outlet__outlet_name')
    list_filter = ('outlet', 'employee')
    fieldsets = (
        (None, {
            'fields': ('employee', 'outlet', 'permissions')
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





@admin.register(Employee)
class PlanAssignmentAccessAdmin(admin.ModelAdmin):
    list_display = ('company','user','first_name','last_name','email','role','employee_code','is_active')
    search_fields = ('company__name','user__username')
    list_filter = ('role','company')
    fieldsets = (
        (None, {
            'fields': ('company','user','first_name','last_name','email','phone_number','address','profile_image','date_of_birth','role','employee_code','is_active')
        }),
    )
    
    





@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'outlet', 'category', 'is_gst_inclusive', 'gst_percentage')
    search_fields = ('name', 'outlet__outlet_name', 'category__name')  # Search includes category name
    list_filter = ('outlet', 'is_gst_inclusive', 'category')  # Add category filter
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'price', 'image', 'description', 'outlet', 'category', 'gst_percentage', 'is_gst_inclusive')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'price', 'is_gst_inclusive')
    search_fields = ('name', 'product__name')
    list_filter = ('is_gst_inclusive', 'product')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('product', 'name', 'price', 'is_gst_inclusive', 'extra_description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    
    




@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'outlet', 'is_enabled', 'start_date', 'end_date', 'open_time', 'close_time')
    list_filter = ('outlet', 'is_enabled', 'start_date', 'end_date')
    search_fields = ('name', 'outlet__name')
    filter_horizontal = ('products',)  # Adds a filter widget for the ManyToManyField
    fieldsets = (
        (None, {
            'fields': ('name', 'outlet', 'is_enabled', 'start_date', 'end_date', 'open_time', 'close_time', 'products')
        }),
    )
    
    



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'outlet')
    search_fields = ('name', 'outlet__name')
    list_filter = ('outlet',)




@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'order_date', 'total_price', 'gst', 'status')
    search_fields = ('order_number',)
    list_filter = ('status', 'order_date')
    ordering = ('-order_date',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'product_variant', 'quantity', 'price')
    search_fields = ('order__order_number', 'product__name', 'product_variant__name')
    list_filter = ('order', 'product', 'product_variant')
    ordering = ('order', 'product')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'order')
    search_fields = ('name', 'phone_number', 'order__order_number')
    list_filter = ('order',)
    ordering = ('name',)






class StockRequestAdmin(admin.ModelAdmin):
    list_display = ('product', 'product_variant', 'status', 'timestamp', 'updated_at', 'outlet')
    list_filter = ('status', 'outlet', 'timestamp')
    search_fields = ('product__name', 'product_variant__name', 'outlet__name')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    raw_id_fields = ('product', 'product_variant', 'outlet')  # Using raw_id_fields for better performance with foreign keys

    # Fields to display in the form when creating/updating a StockRequest
    fields = ('product', 'product_variant', 'status', 'outlet')

# Register the updated admin class
admin.site.register(StockRequest, StockRequestAdmin)



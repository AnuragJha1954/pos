from django.contrib import admin
from .models import (
    Company, Outlet, OutletAccess,
    Plan, PlanAssignment,
    Employee,
    Product, ProductVariant,
    Menu, Category,
    Order, OrderItem, Customer,
    StockRequest, Coupon,
    RazorpayCredential, FCMToken,
    EmployeeCredentials, RefundNote,
    PrinterConfig,
    Table,
    Expense
)

# ================== COMPANY ==================
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'number_of_outlets', 'gst_in', 'number_of_employees')
    search_fields = ('name', 'gst_in')
    list_filter = ('number_of_outlets', 'number_of_employees')


# ================== OUTLET ==================
@admin.register(Outlet)
class OutletAdmin(admin.ModelAdmin):
    list_display = ('outlet_name', 'company', 'gst_number', 'phone_number', 'is_active', 'created_at')
    search_fields = ('outlet_name', 'company__name', 'gst_number')
    list_filter = ('company', 'is_active')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': (
                'company', 'logo', 'gst_number', 'outlet_name',
                'phone_number', 'opening_hours', 'is_active',
                'bank_account_number', 'ifsc_code', 'address'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


# ================== OUTLET ACCESS ==================
@admin.register(OutletAccess)
class OutletAccessAdmin(admin.ModelAdmin):
    list_display = ('employee', 'outlet')
    search_fields = ('employee__first_name', 'outlet__outlet_name')
    list_filter = ('outlet',)


# ================== PLAN ==================
@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('plan_name', 'plan_price', 'price_tenure')
    search_fields = ('plan_name',)


@admin.register(PlanAssignment)
class PlanAssignmentAdmin(admin.ModelAdmin):
    list_display = ('plan', 'user', 'status', 'valid_till')
    list_filter = ('status', 'plan')
    search_fields = ('plan__plan_name', 'user__username')


# ================== EMPLOYEE ==================
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('company', 'user', 'first_name', 'email', 'role', 'employee_code', 'is_active')
    list_filter = ('role', 'company')
    search_fields = ('user__username', 'email')


# ================== CATEGORY ==================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'outlet')
    list_filter = ('outlet',)
    search_fields = ('name',)


# ================== PRODUCT ==================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'outlet', 'category', 'is_veg', 'is_stock_out')
    list_filter = ('outlet', 'category', 'is_veg', 'is_stock_out')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'price', 'is_stock_out')
    list_filter = ('product', 'is_stock_out')
    search_fields = ('name',)


# ================== MENU ==================
@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'outlet', 'is_enabled')
    list_filter = ('outlet', 'is_enabled')
    filter_horizontal = ('products',)


# ================== ORDER INLINE ==================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


# ================== ORDER ==================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number',
        'outlet',
        'table_number',
        'status',
        'total_price',
        'order_date'
    )
    list_filter = ('status', 'outlet', 'order_date')
    search_fields = ('order_number',)
    readonly_fields = ('order_date', 'updated_at')
    ordering = ('-order_date',)
    inlines = [OrderItemInline]


# ================== ORDER ITEM ==================
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'order',
        'product',
        'product_variant',
        'quantity',
        'price',
        'status'
    )
    list_filter = ('status', 'order')
    search_fields = ('order__order_number', 'product__name')


# ================== CUSTOMER ==================
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'order')
    search_fields = ('name', 'phone_number')


# ================== TABLE ==================
@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = (
        'table_number',
        'table_id',
        'outlet',
        'location',
        'status',
        'current_order'
    )
    list_filter = ('status', 'outlet', 'location')
    search_fields = ('table_id', 'table_number')
    ordering = ('table_number',)


# ================== EXPENSE ==================
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'amount',
        'outlet',
        'expense_date'
    )
    list_filter = ('outlet', 'expense_date')
    search_fields = ('title',)
    ordering = ('-expense_date',)


# ================== STOCK ==================
@admin.register(StockRequest)
class StockRequestAdmin(admin.ModelAdmin):
    list_display = ('product', 'product_variant', 'status', 'outlet', 'timestamp')
    list_filter = ('status', 'outlet')
    search_fields = ('product__name',)


# ================== COUPON ==================
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('coupon_code', 'outlet', 'discount_type', 'discount_value', 'is_active')
    list_filter = ('outlet', 'discount_type', 'is_active')
    filter_horizontal = ('products', 'categories')


# ================== RAZORPAY ==================
@admin.register(RazorpayCredential)
class RazorpayCredentialAdmin(admin.ModelAdmin):
    list_display = ('outlet', 'razorpay_client_id')


# ================== PRINTER ==================
@admin.register(PrinterConfig)
class PrinterConfigAdmin(admin.ModelAdmin):
    list_display = ('outlet', 'updated_at')


# ================== SIMPLE REGISTRATIONS ==================
admin.site.register(FCMToken)
admin.site.register(EmployeeCredentials)


# ================== REFUND ==================
@admin.register(RefundNote)
class RefundNoteAdmin(admin.ModelAdmin):
    list_display = ('order', 'refund_title', 'refund_amount', 'created_at')
    search_fields = ('order__order_number',)
    ordering = ('-created_at',)
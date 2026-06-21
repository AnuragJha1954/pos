from django.contrib import admin
from .models import *


# =========================
# INLINES
# =========================

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price','gst')


class OrderPaymentInline(admin.TabularInline):
    model = OrderPayment
    extra = 0


class CustomerInline(admin.TabularInline):
    model = Customer
    extra = 0


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


# =========================
# COMPANY
# =========================

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'number_of_outlets',
        'number_of_employees',
        'gst_in'
    )
    search_fields=('name','gst_in')


# =========================
# OUTLET
# =========================

@admin.register(Outlet)
class OutletAdmin(admin.ModelAdmin):
    list_display=(
        'outlet_name',
        'company',
        'phone_number',
        'gst_number',
        'is_active'
    )
    list_filter=('company','is_active')
    search_fields=('outlet_name','gst_number')
    readonly_fields=('created_at','updated_at')


# =========================
# OUTLET ACCESS
# =========================

@admin.register(OutletAccess)
class OutletAccessAdmin(admin.ModelAdmin):
    list_display=('employee','outlet')
    list_filter=('outlet',)



# =========================
# PLAN
# =========================

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display=(
        'plan_name',
        'plan_price',
        'price_tenure',
        'has_kot'
    )
    list_filter=('price_tenure','has_kot')


@admin.register(PlanAssignment)
class PlanAssignmentAdmin(admin.ModelAdmin):
    list_display=(
        'user',
        'plan',
        'status',
        'valid_till'
    )
    list_filter=('status','plan')


# =========================
# EMPLOYEE
# =========================

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display=(
        'first_name',
        'email',
        'company',
        'role',
        'employee_code',
        'is_active'
    )
    list_filter=('role','company')
    search_fields=('first_name','email')


# =========================
# CATEGORY
# =========================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display=('name','outlet')
    search_fields=('name',)



# =========================
# PRODUCT
# =========================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display=(
        'name',
        'price',
        'category',
        'is_veg',
        'is_stock_out'
    )

    list_filter=(
        'category',
        'is_veg',
        'is_stock_out'
    )

    search_fields=('name',)

    inlines=[ProductVariantInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display=(
        'name',
        'product',
        'price',
        'is_stock_out'
    )


# =========================
# MENU
# =========================

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display=(
        'name',
        'outlet',
        'is_enabled'
    )

    filter_horizontal=('products',)



# =========================
# ORDER
# =========================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display=(
        'order_number',
        'outlet',
        'table_number',
        'status',
        'payment_status',
        'mode',
        'total_price',
        'order_date'
    )

    list_filter=(
        'status',
        'payment_status',
        'mode',
        'outlet'
    )

    search_fields=(
        'order_number',
        'plutus_transaction_reference_id'
    )

    readonly_fields=(
        'order_date',
        'updated_at'
    )

    ordering=('-order_date',)

    inlines=[
        OrderItemInline,
        OrderPaymentInline,
        CustomerInline
    ]


# =========================
# ORDER ITEM
# =========================

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display=(
        'order',
        'product',
        'product_variant',
        'quantity',
        'status'
    )
    list_filter=('status',)


# =========================
# CUSTOMER
# =========================

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display=(
        'name',
        'phone_number',
        'order'
    )
    search_fields=('name','phone_number')


# =========================
# TABLE
# =========================

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display=(
        'table_number',
        'table_id',
        'outlet',
        'status',
        'current_order'
    )
    list_filter=('status','outlet')


# =========================
# KOT
# =========================

@admin.register(KOT)
class KOTAdmin(admin.ModelAdmin):
    list_display=(
        'kot_number',
        'table',
        'order',
        'created_at'
    )

    search_fields=(
        'order__order_number',
    )

    ordering=('-created_at',)



# =========================
# PAYMENTS
# =========================

@admin.register(OrderPayment)
class OrderPaymentAdmin(admin.ModelAdmin):
    list_display=(
        'order',
        'payment_mode',
        'amount',
        'transaction_id',
        'created_at'
    )

    list_filter=('payment_mode',)
    search_fields=('transaction_id',)



# =========================
# EXPENSE
# =========================

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display=(
        'title',
        'amount',
        'outlet',
        'expense_date'
    )

    list_filter=('outlet',)



# =========================
# STOCK REQUEST
# =========================

@admin.register(StockRequest)
class StockRequestAdmin(admin.ModelAdmin):
    list_display=(
        'product',
        'product_variant',
        'status',
        'outlet'
    )

    list_filter=('status',)



# =========================
# COUPONS
# =========================

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display=(
        'coupon_code',
        'discount_type',
        'discount_value',
        'is_active'
    )

    filter_horizontal=(
        'products',
        'categories'
    )


# =========================
# REFUNDS
# =========================

@admin.register(RefundNote)
class RefundNoteAdmin(admin.ModelAdmin):
    list_display=(
        'order',
        'refund_title',
        'refund_amount',
        'created_at'
    )


# =========================
# DEVICES / CONFIG
# =========================

@admin.register(KOTDevice)
class KOTDeviceAdmin(admin.ModelAdmin):
    list_display=(
        'device_id',
        'registered_by',
        'is_logged_in',
        'is_active'
    )


@admin.register(PrinterConfig)
class PrinterConfigAdmin(admin.ModelAdmin):
    list_display=('outlet','updated_at')


@admin.register(RazorpayCredential)
class RazorpayCredentialAdmin(admin.ModelAdmin):
    list_display=(
        'outlet',
        'razorpay_client_id'
    )



admin.site.register(EmployeeCredentials)
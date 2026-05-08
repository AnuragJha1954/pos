import random
import string
from django.db import models
from django.contrib.auth import get_user_model
from datetime import date
from django.conf import settings
from django.utils import timezone
# Create your models here.


class Company(models.Model):
    name = models.CharField(max_length=255)
    number_of_outlets = models.IntegerField( null=True, blank=True)
    number_of_employees = models.IntegerField( null=True, blank=True)
    address = models.TextField( null=True, blank=True)
    gst_in = models.CharField(max_length=15, unique=True, null=True, blank=True)
    
    # Add other company details fields here

    def __str__(self):
        return self.name
    
    



class Outlet(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='outlets')
    logo = models.ImageField(upload_to='logos/')
    gst_number = models.CharField(max_length=50)
    outlet_name = models.CharField(max_length=255)
    address = models.TextField()
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    opening_hours = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    bank_account_number = models.CharField(max_length=20, blank=True, null=True)
    ifsc_code = models.CharField(max_length=11, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.outlet_name


class OutletAccess(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE)
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE)
    permissions = models.JSONField()

    def __str__(self):
        return f'{self.employee} - {self.outlet}'









class Plan(models.Model):
    PLAN_TENURE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually')
    ]

    plan_name = models.CharField(max_length=100)
    plan_price = models.DecimalField(max_digits=10, decimal_places=2)
    price_tenure = models.CharField(max_length=20, choices=PLAN_TENURE_CHOICES)

    # 🔥 ADD-ON (KOT)
    has_kot = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.plan_name} - {self.price_tenure}"

    class Meta:
        verbose_name = 'Plan'
        verbose_name_plural = 'Plans'






class PlanAssignment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired'),
    ]

    plan = models.ForeignKey('Plan', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    valid_till = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"{self.user} - {self.plan} - {self.status}"

    class Meta:
        verbose_name = 'Plan Assignment'
        verbose_name_plural = 'Plan Assignments'











class Employee(models.Model):
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('store_admin', 'Store Admin'),
        ('pos_staff', 'POS Staff'),
    ]

    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100,blank=True, null=True)
    last_name = models.CharField(max_length=100,blank=True, null=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15,blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='employee_profiles/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    employee_code = models.CharField(max_length=8, unique=True, blank=True, null=True)
    permissions = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_role_display()}"
    
    







class Category(models.Model):
    outlet = models.ForeignKey('Outlet', on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name










class Product(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Enter GST percentage.",blank=True, null=True)
    is_gst_inclusive = models.BooleanField(default=False, help_text="Indicates if the price is GST inclusive.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products')  # Add category field
    is_veg = models.BooleanField(default=True, help_text="Indicates if the item is veg.")
    is_stock_out = models.BooleanField(default=False, help_text="True if the product is out of stock")

    def __str__(self):
        return self.name







class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=255, help_text="Variant name, e.g., 'Large', 'Red'.")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_gst_inclusive = models.BooleanField(default=False, help_text="Indicates if the price is GST inclusive.")
    extra_description = models.JSONField(
        blank=True,
        default=list,
        help_text="List of additional attributes such as 'extra spicy', 'sugar free', etc."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_stock_out = models.BooleanField(default=False, help_text="True if the product is out of stock")

    def __str__(self):
        return f"{self.product.name} - {self.name}"
    






class Menu(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='menus')
    name = models.CharField(max_length=255)
    is_enabled = models.BooleanField(default=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    open_time = models.TimeField(blank=True, null=True)
    close_time = models.TimeField(blank=True, null=True)
    products = models.ManyToManyField(Product, blank=True, related_name='menus')

    def __str__(self):
        return f"{self.name} - {self.outlet.outlet_name}"
    















class Order(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),

        # Order placed
        ('pending', 'Pending'),              # Sent to KOT but not started
        ('processing', 'Processing'),        # Kitchen started

        # KOT lifecycle
        ('ready', 'Ready'),                  # All items prepared
        ('completed', 'Completed'),          # KOT closed

        # Billing lifecycle
        ('payment_pending', 'Payment Pending'),
        ('settled', 'Settled'),

        # End states
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    ]
    
    MODE_CHOICES = [
        ('upi', 'UPI'),
        ('cash', 'Cash Payment'),
        ('coupon', 'Coupon'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('initiated', 'Initiated'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Add ForeignKey to Outlet
    outlet = models.ForeignKey('Outlet', on_delete=models.CASCADE, related_name='orders')  # Assuming Outlet model is in the 'qr' app

    order_number = models.CharField(max_length=20, unique=True)  # New field for the order number
    order_date = models.DateTimeField(default=timezone.now)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    gst = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    address = models.TextField(blank=True, null=True)  # New optional address field
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, blank=True, null=True)  # New mode field
    updated_at = models.DateTimeField(auto_now=True)
    
    # 🔥 Table relation (NEW)
    table_number = models.ForeignKey(
        'Table',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    
    # Razorpay-related fields
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)    
    
    # ✅ Optional note field
    note = models.TextField(blank=True, null=True, help_text="Any specific note or instruction for the order.")
    
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    # 🔥 PineLabs Fields
    pine_transaction_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Same as TransactionNumber sent to PineLabs"
    )

    plutus_transaction_reference_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        help_text="PTRN returned by PineLabs"
    )

    pine_payment_mode = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Final payment mode (UPI/Card/etc)"
    )

    pine_response = models.JSONField(
        null=True,
        blank=True,
        help_text="Full PineLabs response for audit/debug"
    )

    # 🔁 Refund / Void Support
    parent_transaction_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Original transaction ID for refund/void"
    )
    
    upi_type = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="UPI provider like gpay, phonepe, paytm"
    )

    def __str__(self):
        return f"Order {self.order_number}"

    
    
    
    
    
    
    
class OrderItem(models.Model):
    ITEM_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('rejected', 'Rejected'),
    ]

    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='items')

    product = models.ForeignKey(
        'Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    product_variant = models.ForeignKey(
        'ProductVariant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gst = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # 🔥 Item-level status (NEW)
    status = models.CharField(
        max_length=20,
        choices=ITEM_STATUS_CHOICES,
        default='processing'
    )

    def __str__(self):
        name = self.product_variant.name if self.product_variant else self.product.name
        return f"{self.quantity} x {name} ({self.status})"
    
    






class Customer(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)  # Assuming a max length for phone numbers
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='customers',null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.phone_number})"
    
    
    
    






class StockRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    product = models.ForeignKey(
        Product, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='stock_requests'
    )
    product_variant = models.ForeignKey(
        ProductVariant, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='stock_requests'
    )
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='PENDING'
    )
    updated_at = models.DateTimeField(auto_now=True)
    outlet = models.ForeignKey('Outlet', on_delete=models.CASCADE, related_name='stock')

    def __str__(self):
        return f"Stock Request for {'Variant' if self.product_variant else 'Product'} {self.product_variant.name if self.product_variant else self.product.name}, Status: {self.status}"









class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('rupees', 'Rupees'),
    ]
    
    outlet = models.ForeignKey('Outlet', on_delete=models.CASCADE, related_name='coupons')  # 👈 ForeignKey to Outlet

    coupon_code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Max discount in ₹ (only applicable for percentage type)"
    )
    min_cart_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    expiry_date = models.DateTimeField(null=True, blank=True)

    products = models.ManyToManyField('Product', blank=True, help_text="Leave empty to apply on all products")
    categories = models.ManyToManyField('Category', blank=True, help_text="Leave empty to apply on all categories")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self):
        return self.expiry_date and timezone.now() > self.expiry_date

    def __str__(self):
        return self.coupon_code






class RazorpayCredential(models.Model):
    outlet = models.OneToOneField(Outlet, on_delete=models.CASCADE, related_name='razorpay_credential')
    razorpay_client_id = models.CharField(max_length=100)
    razorpay_client_secret = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Razorpay Credentials for {self.outlet.outlet_name}"





class FCMToken(models.Model):
    outlet = models.ForeignKey('Outlet', on_delete=models.CASCADE, related_name='fcmtokens')  # 👈 ForeignKey to Outlet
    token = models.CharField(max_length=500)  # Adjust max_length as needed

    def __str__(self):
        return f"FCM Token for {self.outlet.outlet_name}"
    
    




class EmployeeCredentials(models.Model):
    employee = models.OneToOneField('Employee', on_delete=models.CASCADE, related_name='credentials')
    email = email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Credentials for {self.employee}"











class RefundNote(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='refund_notes')
    refund_title = models.CharField(max_length=255)
    refund_description = models.TextField(blank=True, null=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Refund for Order {self.order.order_number} - {self.refund_title}"




class PrinterConfig(models.Model):
    outlet = models.OneToOneField(
        Outlet,
        on_delete=models.CASCADE,
        related_name='printer_config'
    )
    printers = models.JSONField(default=list)  # list of printer names

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Printers for {self.outlet.outlet_name}"



class Table(models.Model):
    TABLE_STATUS_CHOICES = [
        ('empty', 'Empty'),
        ('running', 'Running'),
        ('printing', 'Printing'),
        ('paid', 'Paid'),
        ('running_kot', 'Running KOT'),
        ('pending_counter_confirmation', 'Pending Counter Confirmation'), 
    ]

    outlet = models.ForeignKey('Outlet', on_delete=models.CASCADE, related_name='tables')
    table_number = models.PositiveIntegerField()
    table_id = models.CharField(max_length=20, unique=True)
    location = models.CharField(max_length=50)

    status = models.CharField(max_length=50, choices=TABLE_STATUS_CHOICES, default='empty')

    created_at = models.DateTimeField(auto_now_add=True)
    current_order = models.ForeignKey(
        'Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='table_current_orders'
    )

    def __str__(self):
        return f"Table {self.table_number}"
    
    





class Expense(models.Model):
    outlet = models.ForeignKey('Outlet', on_delete=models.CASCADE, related_name='expenses')

    title = models.CharField(max_length=255, help_text="Expense title (e.g., Milk Purchase)")
    description = models.TextField(blank=True, null=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    expense_date = models.DateTimeField(default=timezone.now)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - ₹{self.amount}"






class KOT(models.Model):
    table = models.ForeignKey('Table', on_delete=models.CASCADE, related_name='kots')
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='kots')

    kot_number = models.PositiveIntegerField()  # 1, 2, 3...
    
    items = models.JSONField(
        help_text="[{product_id, product_name, quantity}]"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"KOT {self.kot_number} - Table {self.table.table_number}"






class OrderPayment(models.Model):
    PAYMENT_MODE_CHOICES = [
        ('upi', 'UPI'),
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('coupon', 'Coupon'),
    ]

    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='payments')

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES)

    transaction_id = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order.order_number} - {self.payment_mode} - {self.amount}"





class KOTDevice(models.Model):
    device_id = models.CharField(max_length=100, unique=True)

    registered_by = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    registered_at = models.DateTimeField(auto_now_add=True)

    is_logged_in = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.device_id}"



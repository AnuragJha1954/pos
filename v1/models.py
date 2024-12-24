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
    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Enter GST percentage.")
    is_gst_inclusive = models.BooleanField(default=False, help_text="Indicates if the price is GST inclusive.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products')  # Add category field

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
        return f"{self.name} - {self.outlet.name}"
    















class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    MODE_CHOICES = [
        ('upi', 'UPI'),
        ('cash', 'Cash Payment'),
        ('coupon', 'Coupon'),
    ]
    
    # Add ForeignKey to Outlet
    outlet = models.ForeignKey('Outlet', on_delete=models.CASCADE, related_name='orders')  # Assuming Outlet model is in the 'qr' app

    order_number = models.CharField(max_length=20, unique=True)  # New field for the order number
    order_date = models.DateTimeField(default=timezone.now)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    gst = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    address = models.TextField(blank=True, null=True)  # New optional address field
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, blank=True, null=True)  # New mode field
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_number}"

    
    
    
    
    
    
    
class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True)  # Optional ForeignKey to Product
    product_variant = models.ForeignKey('ProductVariant', on_delete=models.SET_NULL, null=True, blank=True)  # Optional ForeignKey to ProductVariant
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # New field
    gst = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # New field

    def __str__(self):
        return f"{self.quantity} of {self.product_variant.name if self.product_variant else self.product.name} in order {self.order.id}"

    
    
    






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








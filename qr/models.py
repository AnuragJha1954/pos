from django.db import models
from django.contrib.postgres.fields import JSONField  # For PostgreSQL JSONField
from django.utils import timezone
# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.ImageField(upload_to='category_icons/', blank=True, null=True)

    def __str__(self):
        return self.name
    
    
    
    

class Product(models.Model):
    name = models.CharField(max_length=150)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.name








class ProductVariant(models.Model):
    name = models.CharField(max_length=150)
    variant_description = models.TextField(blank=True, null=True)
    details = models.JSONField(blank=True, null=True)  # Optional JSON field
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    variant_image = models.ImageField(upload_to='variant_images/', blank=True, null=True)
    variant_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.product.name}"
    
    
    




class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=20, unique=True)  # New field for the order number
    order_date = models.DateTimeField(default=timezone.now)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    gst = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    address = models.TextField(blank=True, null=True)  # New optional address field

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
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='customers')

    def __str__(self):
        return f"{self.name} ({self.phone_number})"
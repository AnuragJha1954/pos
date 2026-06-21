from django.db import models
from django.utils import timezone
from v1.models import Outlet, Product, ProductVariant

class Supplier(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='suppliers')
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.outlet.outlet_name}"

class InventoryItem(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('l', 'Liter'),
        ('ml', 'Milliliter'),
        ('pcs', 'Pieces'),
        ('box', 'Box'),
        ('pkt', 'Packet'),
        ('other', 'Other'),
    ]

    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='inventory_items')
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, blank=True, null=True, help_text="Stock Keeping Unit (optional)")
    linked_product = models.ForeignKey(
        Product, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='inventory_links',
        help_text="Link to a sellable product if this item represents a finished good."
    )
    linked_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='inventory_links',
        help_text="Link to a sellable product variant if applicable."
    )
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='pcs')
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    low_stock_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.current_stock} {self.unit})"

class StockTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('purchase', 'Purchase (Stock In)'),
        ('sale', 'Sale (Stock Out)'),
        ('adjustment', 'Adjustment'),
        ('return', 'Return (Stock In)'),
        ('damage', 'Damage/Waste (Stock Out)'),
    ]

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Positive for in, negative for out")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, blank=True, null=True, related_name='transactions')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.transaction_type} - {self.quantity} {self.item.unit} of {self.item.name}"

from django.contrib import admin
from .models import Category, Product, ProductVariant, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'gst_percent')
    search_fields = ('name',)
    list_filter = ('category',)
    ordering = ('name',)

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'variant_description', 'variant_price')
    search_fields = ('name', 'product__name')
    list_filter = ('product',)
    ordering = ('name',)

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
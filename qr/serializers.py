from rest_framework import serializers
from .models import (
    Category,
    Product,
    ProductVariant,
    Order,
    OrderItem
)



class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'icon')  # Include fields you want to serialize
        
        
        
        
        
        
class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ('id', 'name', 'variant_description', 'details', 'variant_image', 'variant_price')





class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, source='productvariant_set', read_only=True)  # Nested serializer

    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'image', 'description', 'price', 'gst_percent', 'variants')







class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'product_variant', 'quantity']  # Remove price, total_price, and gst

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)  # List of order items

    class Meta:
        model = Order
        fields = ['order_date', 'total_price', 'gst', 'items']  # Remove order_number

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = Order.objects.create(**validated_data)

        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        return order

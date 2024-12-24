from rest_framework import serializers
from v1.models import Order, OrderItem, Customer

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_variant_name = serializers.CharField(source='product_variant.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'product_variant_name', 'quantity', 'price', 'total_price', 'gst']
        ref_name = 'KotOrderItemSerializer'
        
        
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone_number']
        ref_name = 'KotCustomerSerializer'

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customers = CustomerSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['order_number', 'order_date', 'total_price', 'gst', 'status', 'address', 'mode', 'items', 'customers']
        ref_name = 'KotOrderSerializer'
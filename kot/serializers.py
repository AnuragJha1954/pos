from rest_framework import serializers
from v1.models import (
    Order,
    OrderItem,
    Customer,
    ProductVariant,
    Employee
)
from users.models import CustomUser

class CustomUserCounterLoginSerializer(serializers.Serializer):
    username = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.CharField()

    def validate(self, data):
        email = data.get('username')
        password = data.get('password')
        role = data.get('role')

        if not email or not password or not role:
            raise serializers.ValidationError("Email, password, and role are required.")

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        # Check if the password matches
        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password.")

        # Check if the user is associated with an employee having the provided role
        if not Employee.objects.filter(user=user, role=role).exists():
            raise serializers.ValidationError("User does not have the specified role.")

        data['user'] = user
        return data


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
        fields = ['order_number', 'order_date', 'total_price', 'gst', 'status', 'address', 'mode', 'items', 'customers','table_number']
        ref_name = 'KotOrderSerializer'


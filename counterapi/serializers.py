from rest_framework import serializers
from v1.models import (
    Company,
    OutletAccess,
    Outlet,
    Category,
    Product,
    ProductVariant,
    Order,
    OrderItem,
    Customer,
    StockRequest,
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












class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'name', 'price', 'is_gst_inclusive', 'extra_description', 'created_at', 'updated_at']

class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    category = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'description', 'gst_percentage', 
            'is_gst_inclusive', 'created_at', 'updated_at', 
            'category', 'variants', 'image_url'
        ]

    def get_image_url(self, obj):
        # Return the absolute URL of the image if it exists
        if obj.image:
            return obj.image.url
        return None    











class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    variant_name = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'product', 
            'product_variant', 
            'quantity', 
            'price', 
            'total_price', 
            'gst', 
            'product_name', 
            'variant_name'
        ]
        ref_name = 'CounterOrderItemSerializer'

    def get_product_name(self, obj):
        return obj.product.name if obj.product else None

    def get_variant_name(self, obj):
        return obj.product_variant.name if obj.product_variant else None

            
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['outlet', 'order_number', 'order_date', 'total_price', 'gst', 'status', 'address', 'mode', 'items']
        depth=1
        ref_name = 'CounterOrderSerializer'

    def get_outlet_logo_url(self, obj):
        outlet_logo_url = None
        if obj.outlet and obj.outlet.logo:
            request = self.context.get('request')
            if request:
                outlet_logo_url = request.build_absolute_uri(obj.outlet.logo.url)
        return outlet_logo_url


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['name', 'phone_number', 'order']
        ref_name = 'CounterCustomerSerializer'













class OrderItemListSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_variant_name = serializers.CharField(source='product_variant.name', read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    gst = serializers.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        model = OrderItem
        fields = ['product_name', 'product_variant_name', 'quantity', 'price', 'total_price', 'gst']


class CustomerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['name', 'phone_number']

class OrderListSerializer(serializers.ModelSerializer):
    items = OrderItemListSerializer(many=True, read_only=True)
    customer = CustomerListSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['order_number', 'order_date', 'total_price', 'gst', 'status', 'mode', 'address', 'items', 'customer']
        
    
    





class StockRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockRequest
        fields = ['product', 'product_variant', 'outlet']
        read_only_fields = ['status', 'timestamp', 'updated_at']

    def validate(self, data):
        # Ensure that either product or product_variant is provided
        if not data.get('product') and not data.get('product_variant'):
            raise serializers.ValidationError("Either product or product_variant must be provided.")
        return data

from rest_framework import serializers
from .models import (
    Outlet,
    OutletAccess, 
    Employee,
    Plan,
    PlanAssignment,
    Product,
    ProductVariant,
    Menu,
    Category,
    StockRequest,
    EmployeeCredentials,
    Order,
    OrderItem, 
    Customer,
    RefundNote,
    Expense,
    Table
)
from users.models import CustomUser



import random
import string

def generate_random_password(length=10):
    characters = (
        string.ascii_letters +   # a-zA-Z
        string.digits +          # 0-9
        "!@#$%^&*()_+"           # special chars
    )
    return ''.join(random.choice(characters) for _ in range(length))


class OutletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Outlet
        fields = '__all__'
        
        
        
        
        
class EmployeeCreateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=15, required=False, allow_blank=True)
    profile_image = serializers.ImageField(required=False)
    address = serializers.CharField(required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    role = serializers.ChoiceField(choices=Employee.ROLE_CHOICES)
    permissions = serializers.JSONField(required=False)

    def create_employee_user(self, validated_data, company):
        # Create a unique username from the first and last name
        username = f"{validated_data['first_name']}_{validated_data['last_name']}".lower()

        # Generate a random password
        password = generate_random_password()

        # Create the CustomUser instance
        user = CustomUser.objects.create_user(
            username=username,
            email=validated_data['email'],
            phone_number=validated_data.get('phone_number'),
            company=company,
            password=password
        )
        user.plain_password = password
        user.save()

        return user
















class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'product','name', 'price', 'is_gst_inclusive', 'extra_description']

    def create(self, validated_data):
        # Create and return a new ProductVariant instance
        return ProductVariant.objects.create(**validated_data)






class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())  # Add category field
    variants = ProductVariantSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'image', 'description', 'outlet', 'is_gst_inclusive','category','is_veg','variants']
        
    def create(self, validated_data):
        # Create and return a new Product instance
        return Product.objects.create(**validated_data)






class MenuSerializer(serializers.ModelSerializer):
    products = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        many=True,
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Menu
        fields = ['id', 'name', 'is_enabled', 'start_date', 'end_date', 'open_time', 'close_time', 'outlet', 'products']
    
    def create(self, validated_data):
        products_data = validated_data.pop('products', [])
        menu = Menu.objects.create(**validated_data)
        menu.products.set(products_data)
        return menu





class MenuListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = ['id', 'name', 'is_enabled', 'start_date', 'end_date', 'open_time', 'close_time']







class ProductVariantListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'name', 'price', 'is_gst_inclusive', 'extra_description']
        
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

class ProductListSerializer(serializers.ModelSerializer):
    variants = ProductVariantListSerializer(many=True, read_only=True)
    category = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'image', 'description', 'is_gst_inclusive', 'variants','category']
        
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

class MenuDetailSerializer(serializers.ModelSerializer):
    products = ProductListSerializer(many=True, read_only=True)
    
    class Meta:
        model = Menu
        fields = ['id', 'name', 'is_enabled', 'start_date', 'end_date', 'open_time', 'close_time', 'products']









class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'outlet']









class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address', 'profile_image', 'date_of_birth', 'role', 'is_active', 'employee_code']







class StockRequestListSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockRequest
        fields = ['id', 'product', 'product_variant', 'status', 'timestamp', 'updated_at']



class ApproveStockRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockRequest
        fields = ['id', 'status']

    def update(self, instance, validated_data):
        # Approve the stock request by setting status to 'APPROVED'
        instance.status = 'APPROVED'
        instance.save()
        return instance






class EmployeeListSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id",
            "user_id",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "address",
            "role",
            "role_display",
            "employee_code",
            "is_active",
            "permissions",
        ]






class EmployeePermissionsUpdateSerializer(serializers.Serializer):
    permissions = serializers.DictField(child=serializers.BooleanField(), required=True)





class EmployeeCredentialsSerializer(serializers.ModelSerializer):
    employee_id = serializers.IntegerField(source='employee.id', read_only=True)

    class Meta:
        model = EmployeeCredentials
        fields = ['employee_id', 'email', 'password', 'created_at']





class ManageEmployeeCredentialsSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, max_length=128)
    
    
    
    



class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_variant', 'quantity', 'price', 'total_price', 'gst']
        ref_name = 'PanelOrderItemSerializer'

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['name', 'phone_number']
        ref_name = 'PanelCustomerSerializer'

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    outlet_id = serializers.IntegerField(source='outlet.id', read_only=True)
    outlet_name = serializers.CharField(source='outlet.outlet_name', read_only=True)
    customers = CustomerSerializer(many=True, read_only=True)
    ref_name = 'PanelOrderSerializer'

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'order_date', 'total_price', 'gst', 'status',
            'address', 'mode', 'updated_at', 'table_number',
            'outlet_id', 'outlet_name', 'customers', 'items','note'
        ]








# Serializers start for particular order details

class ProductInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'image', 'description', 'is_gst_inclusive', 'is_veg']

class ProductVariantInlineSerializer(serializers.ModelSerializer):
    product = ProductInlineSerializer()

    class Meta:
        model = ProductVariant
        fields = ['id', 'name', 'price', 'is_gst_inclusive', 'extra_description', 'product']


class OrderItemDetailSerializer(serializers.ModelSerializer):
    product = ProductInlineSerializer()
    product_variant = ProductVariantInlineSerializer()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_variant', 'quantity', 'price', 'total_price', 'gst']


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['name', 'phone_number']


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemDetailSerializer(many=True)
    customers = CustomerSerializer(many=True)
    outlet_id = serializers.IntegerField(source='outlet.id')
    outlet_name = serializers.CharField(source='outlet.outlet_name')

    class Meta:
        model = Order
        fields = [
            'order_number', 'order_date', 'total_price', 'gst', 'status', 'mode',
            'table_number', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature',
            'items', 'customers', 'outlet_id', 'outlet_name', 'note'
        ]





class OrderBillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['order_number']






class RefundNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundNote
        fields = ['refund_title', 'refund_description', 'refund_amount']




class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = '__all__'


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'


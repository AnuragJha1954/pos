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
    StockRequest
)
from users.models import CustomUser

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

    def create_employee_user(self, validated_data, company):
        # Create a unique username from the first and last name
        username = f"{validated_data['first_name']}_{validated_data['last_name']}".lower()

        # Generate a random password
        password = CustomUser.objects.make_random_password()

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









class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())  # Add category field
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'image', 'description', 'outlet', 'is_gst_inclusive','category']
        
    def create(self, validated_data):
        # Create and return a new Product instance
        return Product.objects.create(**validated_data)






class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'product', 'price', 'is_gst_inclusive', 'extra_description']

    def create(self, validated_data):
        # Create and return a new ProductVariant instance
        return ProductVariant.objects.create(**validated_data)









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


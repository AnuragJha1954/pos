from rest_framework import serializers

from v1.models import (
    Category,
    Product,
    ProductVariant,
    Outlet,
    Order,
    OrderItem,
    Coupon, 
    RazorpayCredential,
    Company
)

from .models import (
    QRCustomization,
    SpecialMenu,
    AdvertisementBanner,
    OutletTableConfiguration,
    TableQR
)



# class CategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Category
#         fields = ('id', 'name', 'icon')  # Include fields you want to serialize
        
        
        
        
        
        
class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'name', 'price', 'is_gst_inclusive', 'extra_description', 'created_at', 'updated_at','is_stock_out']

    # def to_representation(self, instance):
    #     """Adjust the variant price based on GST inclusion."""
    #     data = super().to_representation(instance)
        
    #     # Check if GST is inclusive and adjust the price accordingly
    #     if instance.is_gst_inclusive:
    #         gst_amount = instance.price * (instance.product.gst_percentage / 100)
    #         data['price_with_gst'] = instance.price  # Price already includes GST
    #     else:
    #         gst_amount = instance.price * (instance.product.gst_percentage / 100)
    #         data['price_with_gst'] = instance.price + gst_amount  # Add GST to price
        
    #     return data


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)  # Nested serializer for variants
    image_url = serializers.SerializerMethodField()
    category = serializers.CharField(source='category.name', read_only=True)


    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'description', 'gst_percentage', 
            'is_gst_inclusive', 'created_at', 'updated_at', 
            'category', 'variants', 'image_url', 'is_veg', 'is_stock_out'
        ]


    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request is not None:
            return request.build_absolute_uri(obj.image.url)
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
        fields = ['outlet', 'order_number', 'order_date', 'total_price', 'gst', 'status', 'address', 'mode', 'items','table_number']
        depth=1
        ref_name = 'CounterOrderSerializer'

    def get_outlet_logo_url(self, obj):
        outlet_logo_url = None
        if obj.outlet and obj.outlet.logo:
            request = self.context.get('request')
            if request:
                outlet_logo_url = request.build_absolute_uri(obj.outlet.logo.url)
        return outlet_logo_url
    





class CouponSerializer(serializers.ModelSerializer):
    products = serializers.StringRelatedField(many=True)
    categories = serializers.StringRelatedField(many=True)

    class Meta:
        model = Coupon
        fields = [
            'coupon_code', 'discount_type', 'discount_value',
            'max_discount_amount', 'min_cart_value', 'expiry_date',
            'products', 'categories', 'is_active'
        ]



class RazorpayCredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = RazorpayCredential
        fields = ['razorpay_client_id', 'razorpay_client_secret']




class QRCustomizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = QRCustomization
        fields = ['qr_tagline', 'qr_logo', 'theme_color','color_palette']
        
    def get_qr_logo(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.qr_logo.url) if obj.qr_logo and request else None

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['name', 'address']
        ref_name = 'QrCompanySerializer'

class OutletSerializer(serializers.ModelSerializer):
    company_details = CompanySerializer(source='company')
    qr_customization_details = QRCustomizationSerializer(source='qr_customization', many=False)

    class Meta:
        model = Outlet
        fields = [
            'outlet_name', 'address', 'phone_number', 'gst_number',
            'opening_hours', 'is_active','logo',
            'company_details', 'qr_customization_details'
        ]
        ref_name = 'QrOutletSerializer'
        
        
        def get_logo(self, obj):
            request = self.context.get('request')
            return request.build_absolute_uri(obj.logo.url) if obj.logo and request else None







class AdvertisementBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdvertisementBanner
        fields = ['image_url', 'redirect_url']







class SpecialMenuSerializer(serializers.ModelSerializer):
    products = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        many=True
    )

    class Meta:
        model = SpecialMenu
        fields = ['id', 'name', 'products']

    def validate_products(self, value):
        if len(value) > 5:
            raise serializers.ValidationError("A Special Menu can contain a maximum of 5 products.")
        return value






class TableQRSerializer(serializers.ModelSerializer):
    table_number = serializers.IntegerField(required=False)
    qr_image = serializers.SerializerMethodField()

    class Meta:
        model = TableQR
        fields = ['table_number', 'qr_image']

    def get_qr_image(self, obj):
        request = self.context.get('request')
        if obj.qr_image and request:
            return request.build_absolute_uri(obj.qr_image.url)
        elif obj.qr_image:
            return obj.qr_image.url
        return None



class OutletTableConfigurationSerializer(serializers.Serializer):
    number_of_tables = serializers.IntegerField(min_value=0)

    def validate_number_of_tables(self, value):
        if value < 0:
            raise serializers.ValidationError("Number of tables must be 0 or more.")
        return value


from rest_framework import serializers

from v1.models import (
    Category,
    Product,
    ProductVariant,
    Outlet,
    Order,
    OrderItem,
    Coupon
    
)



# class CategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Category
#         fields = ('id', 'name', 'icon')  # Include fields you want to serialize
        
        
        
        
        
        
class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'name', 'price', 'is_gst_inclusive', 'extra_description', 'created_at', 'updated_at']

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
            'category', 'variants', 'image_url', 'is_veg'
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





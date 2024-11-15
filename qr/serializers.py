from rest_framework import serializers

from v1.models import (
    Category,
    Product,
    ProductVariant,
    Outlet,
    Order,
    OrderItem
    
)



# class CategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Category
#         fields = ('id', 'name', 'icon')  # Include fields you want to serialize
        
        
        
        
        
        
class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ('id', 'name', 'extra_description', 'price', 'is_gst_inclusive', 'variant_image')

    def to_representation(self, instance):
        """Adjust the variant price based on GST inclusion."""
        data = super().to_representation(instance)
        
        # Check if GST is inclusive and adjust the price accordingly
        if instance.is_gst_inclusive:
            gst_amount = instance.price * (instance.product.gst_percentage / 100)
            data['price_with_gst'] = instance.price  # Price already includes GST
        else:
            gst_amount = instance.price * (instance.product.gst_percentage / 100)
            data['price_with_gst'] = instance.price + gst_amount  # Add GST to price
        
        return data


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, source='variants', read_only=True)  # Nested serializer for variants

    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'outlet', 'price', 'image', 'description', 'gst_percentage', 'is_gst_inclusive', 'variants')

    def to_representation(self, instance):
        """Adjust the product price based on GST inclusion."""
        data = super().to_representation(instance)

        # Access request object from context
        request = self.context.get('request')

        # Check if GST is inclusive and adjust the price accordingly
        if instance.is_gst_inclusive:
            gst_amount = instance.price * (instance.gst_percentage / 100)
            data['price_with_gst'] = instance.price  # Price already includes GST
        else:
            gst_amount = instance.price * (instance.gst_percentage / 100)
            data['price_with_gst'] = instance.price + gst_amount  # Add GST to price
        
        # Update the product image URL
        if instance.image:
            data['image'] = request.build_absolute_uri(instance.image.url)
        
        # Update variant image URLs
        for variant in data.get('variants', []):
            if variant.get('variant_image'):
                variant['variant_image'] = request.build_absolute_uri(variant['variant_image'])

        return data







class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'product_variant', 'quantity', 'price', 'total_price', 'gst']  # Include price, total_price, and gst if needed

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)  # List of order items
    outlet = serializers.PrimaryKeyRelatedField(queryset=Outlet.objects.all())  # Added outlet field

    class Meta:
        model = Order
        fields = ['order_number', 'order_date', 'total_price', 'gst', 'items', 'mode', 'outlet']  # Include outlet field

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        outlet_data = validated_data.pop('outlet')  # Extract outlet from validated_data

        # Create the order and associate with the outlet
        order = Order.objects.create(**validated_data, outlet=outlet_data)

        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        return order

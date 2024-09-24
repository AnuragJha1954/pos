from django.shortcuts import render

import random
import string

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.shortcuts import get_object_or_404

from .models import (
    Category,
    Product,
    ProductVariant,
    Order,
    OrderItem,
    Customer
)

from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductVariantSerializer,
    OrderItemSerializer,
    OrderSerializer
)



# Create your views here.


@api_view(['GET'])
@swagger_auto_schema(
    operation_summary="List all categories",
    operation_description="Retrieve a list of all categories with their names and icons.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'error': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Indicates if there was an error'),
                'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Detailed error message'),
                'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of categories'),
                'categories': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_OBJECT, properties=CategorySerializer().get_fields())
                ),
            },
        )
    }
)
@permission_classes([AllowAny])
def category_list(request):
    try:
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        response_data = {
            'error': False,
            'detail': 'Categories retrieved successfully',
            'count': categories.count(),
            'categories': serializer.data
        }
        return Response(response_data)
    except Exception as e:
        response_data = {
            'error': True,
            'detail': str(e),
            'count': 0,
            'categories': []
        }
        return Response(response_data, status=500)








@api_view(['GET'])
@swagger_auto_schema(
    operation_summary="List all products",
    operation_description="Retrieve a list of all products with their details and associated variants. Optionally filter by category name using case-insensitive containment.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'error': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Indicates if there was an error'),
                'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Detailed error message'),
                'page_number': openapi.Schema(type=openapi.TYPE_INTEGER, description='Current page number'),
                'next': openapi.Schema(type=openapi.TYPE_STRING, description='URL of the next page'),
                'products': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_OBJECT, properties=ProductSerializer().get_fields())
                ),
            },
        )
    }
)
@permission_classes([AllowAny])
def product_list(request):
    try:
        category_name = request.query_params.get('category_name', None)
        products = Product.objects.all()

        if category_name:
            products = products.filter(category__name__icontains=category_name)

        # Serialize the products without pagination
        serializer = ProductSerializer(products, many=True)

        # Generate absolute URLs for product images and variant images
        for product in serializer.data:
            # Update the product image URL
            if product.get('image'):
                product['image'] = request.build_absolute_uri(product['image'])
            
            # Check for variants and update their image URLs
            if 'variants' in product:
                for variant in product['variants']:
                    if variant.get('variant_image'):
                        variant['variant_image'] = request.build_absolute_uri(variant['variant_image'])

        response_data = {
            'error': False,
            'detail': 'Products retrieved successfully',
            'products': serializer.data
        }
        return Response(response_data, status=200)
    except Exception as e:
        response_data = {
            'error': True,
            'detail': str(e),
            'products': []
        }
        return Response(response_data, status=500)
    
    
    









def generate_order_number(length=12):
    """Generate a random order number with uppercase letters and digits."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# {
#     "order_date": "2024-09-18T12:00:00Z",
#     "total_price": "150.00",
#     "gst": "18.00",
#     "status": "PENDING",
#     "address": "123 Main St, Anytown, AT 12345",
#     "customer": {
#         "name": "John Doe",
#         "phone": "999999999"
#     },
#     "items": [
#         {
#             "product": 1,
#             "quantity": 2
#         },
#         {
#             "product_variant": 5,
#             "quantity": 1
#         }
#     ]
# }




@api_view(['POST'])
@swagger_auto_schema(
    operation_summary="Place an order",
    operation_description="Create a new order with the provided details and items. Order number is generated randomly.",
    request_body=OrderSerializer,
    responses={
        201: OrderSerializer,
        400: openapi.Response('Bad Request', openapi.Schema(type=openapi.TYPE_OBJECT, properties={
            'error': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Indicates if there was an error'),
            'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Detailed error message')
        })),
    }
)
@permission_classes([AllowAny])
def place_order(request):
    serializer = OrderSerializer(data=request.data)

    if serializer.is_valid():
        order_data = serializer.validated_data
        order_data['order_number'] = generate_order_number()

        # Remove items from order_data, as they should be handled separately
        items_data = request.data.get('items', [])
        
        # Handle the creation of the order
        order = Order.objects.create(
            order_number=order_data['order_number'],
            order_date=order_data['order_date'],
            total_price=order_data['total_price'],
            gst=order_data['gst']
        )

        # Extract customer data and create a Customer associated with the created order
        customer_data = request.data.get('customer', {})
        customer = Customer.objects.create(
            name=customer_data.get('name'),
            phone_number=customer_data.get('phone'),
            order=order  # Associate the customer with the created order
        )

        # Process the order items
        items_list = []  # To store item details for the response
        for item_data in items_data:
            product = None
            product_variant = None
            price = 0.0
            gst_percent = 0.0
            total_price = 0.0
            gst_amount = 0.0
            product_name = None
            product_variant_name = None

            # Fetch product or product variant
            if 'product' in item_data:
                product = get_object_or_404(Product, id=item_data['product'])
                price = product.price
                gst_percent = product.gst_percent
                product_name = product.name  # Get the product name
            elif 'product_variant' in item_data:
                product_variant = get_object_or_404(ProductVariant, id=item_data['product_variant'])
                product = product_variant.product
                price = product_variant.variant_price
                gst_percent = product.gst_percent
                product_variant_name = product_variant.name  # Get the product variant name

            # Calculate total price and GST for the item
            quantity = item_data['quantity']
            total_price = price * quantity
            gst_amount = (gst_percent / 100) * total_price

            # Create the order item associated with the order
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                product_variant=product_variant,
                quantity=quantity,
                price=price,
                total_price=total_price,
                gst=gst_amount
            )

            # Append item details for the response
            items_list.append({
                'product_name': product_name,
                'product_variant_name': product_variant_name,
                'quantity': item_data['quantity'],
                'price': price,
                'total_price': total_price,
                'gst': gst_amount,
            })

        # Serialize the entire order including customer and items
        order_details = {
            'error': False,
            'detail': 'Order placed successfully',
            'order_number': order.order_number,
            'customer': {
                'name': customer.name,
                'phone_number': customer.phone_number
            },
            'items': items_list
        }

        return Response(order_details, status=status.HTTP_201_CREATED)

    # Return detailed validation errors if the serializer is invalid
    return Response({
        'error': True,
        'detail': 'Validation failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

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

from v1.models import (
    Outlet,
    Category,
    Product,
    ProductVariant,
    Order,
    OrderItem,
    Customer
)

from .serializers import (
    ProductSerializer,
    ProductVariantSerializer,
    OrderItemSerializer,
    OrderSerializer
)



# Create your views here.

@swagger_auto_schema(
    method='get',
    operation_description="Fetch categories for a specific outlet.",
    responses={
        200: openapi.Response(
            description="Categories fetched successfully.",
            examples={
                "application/json": {
                    "error": False,
                    "detail": "Categories fetched successfully.",
                    "categories": ["Category 1", "Category 2"],
                    "total_count": 2
                }
            }
        ),
        404: "Outlet not found."
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def category_list(request,outlet_id):
    try:
        # Check if the outlet exists
        outlet = Outlet.objects.get(id=outlet_id)

        # Get the categories for the given outlet and extract only the names
        categories = Category.objects.filter(outlet=outlet).values_list('name', flat=True)

        return Response({
            "error": False,
            "detail": "Categories fetched successfully.",
            "categories": list(categories),
            "total_count": categories.count()
        }, status=status.HTTP_200_OK)

    except Outlet.DoesNotExist:
        return Response({
            "error": True,
            "detail": "Outlet not found."
        }, status=status.HTTP_404_NOT_FOUND)








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

        # Apply category filter if present
        if category_name:
            products = products.filter(category__name__icontains=category_name)

        # Serialize the products without pagination
        serializer = ProductSerializer(products, many=True, context={'request': request})

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
def place_order(request, outlet_id):
    # Fetch the outlet from the URL parameter
    outlet = get_object_or_404(Outlet, id=outlet_id)

    # Add the outlet to the request data for the serializer
    request.data['outlet'] = outlet.id

    # Initialize the serializer with the data and validate
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
            mode=order_data['mode'],
            total_price=order_data['total_price'],
            gst=order_data['gst'],
            outlet=outlet  # Associate the outlet with the order
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
                gst_percent = product.gst_percentage
                product_name = product.name  # Get the product name
                
                # If GST is not inclusive, calculate the price including GST
                if not product.is_gst_inclusive:
                    gst_amount = (gst_percent / 100) * price
                    total_price = price + gst_amount  # Add GST to price
                else:
                    total_price = price  # Price already includes GST

            elif 'product_variant' in item_data:
                product_variant = get_object_or_404(ProductVariant, id=item_data['product_variant'])
                product = product_variant.product
                price = product_variant.price
                gst_percent = product.gst_percentage
                product_variant_name = product_variant.name  # Get the product variant name
                
                # If GST is not inclusive, calculate the price including GST
                if not product_variant.is_gst_inclusive:
                    gst_amount = (gst_percent / 100) * price
                    total_price = price + gst_amount  # Add GST to price
                else:
                    total_price = price  # Price already includes GST

            # Calculate total price for the quantity and GST for the item
            quantity = item_data['quantity']
            total_price = total_price * quantity
            gst_amount = (gst_percent / 100) * total_price if not product.is_gst_inclusive else 0

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
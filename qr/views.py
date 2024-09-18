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

from .models import (
    Category,
    Product,
    ProductVariant,
    Order,
    OrderItem
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

        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 10  # Set the number of products per page
        paginated_products = paginator.paginate_queryset(products, request)
        
        serializer = ProductSerializer(paginated_products, many=True)
        response_data = {
            'error': False,
            'detail': 'Products retrieved successfully',
            'page_number': paginator.page.number,
            'next': paginator.get_next_page_link(),
            'products': serializer.data
        }
        return paginator.get_paginated_response(response_data)
    except Exception as e:
        response_data = {
            'error': True,
            'detail': str(e),
            'page_number': 1,
            'next': None,
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
#     "items": [
#         {
#             "product": 1,
#             "quantity": 2,
#             "price": "50.00"
#         },
#         {
#             "product_variant": 5,
#             "quantity": 1,
#             "price": "25.00"
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
        
        # Handle the creation of the order
        order = Order.objects.create(**order_data)
        
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
    
    return Response({
        'error': True,
        'detail': 'Invalid data',
    }, status=status.HTTP_400_BAD_REQUEST)
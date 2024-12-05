import random
import string

from decimal import Decimal

from django.shortcuts import render
from django.core.mail import send_mail
from django.utils import timezone

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination

from datetime import timedelta

from .serializers import ( 
    CustomUserCounterLoginSerializer,
    ProductSerializer,
    OrderItemSerializer,
    OrderSerializer,
    CustomerSerializer,
    OrderListSerializer,
    OrderItemListSerializer,
    CustomerListSerializer,
    StockRequestSerializer
    
)

from users.models import CustomUser
from v1.models import (
    Company,
    Outlet,
    OutletAccess,
    Category,
    Product,
    ProductVariant,
    Order,
    OrderItem, 
    Customer,
    StockRequest,
    Employee
    )






# Create your views here.
@swagger_auto_schema(
    method="post",
    request_body=CustomUserCounterLoginSerializer,
    responses={
        status.HTTP_200_OK: "User Logged in successfully",
        status.HTTP_400_BAD_REQUEST: "Invalid credentials",
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def user_login(request):
    try:
        if request.method == "POST":
            serializer = CustomUserCounterLoginSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data["user"]
                token, _ = Token.objects.get_or_create(user=user)

                # Generate slug from first name and last name
                slug = (user.first_name + user.last_name).lower().replace(" ", "")

                # Get general user details
                user_details = {
                    "id": user.id,
                    "username": user.username,
                    "name": f"{user.first_name} {user.last_name}",
                    "email": user.email,
                    "slug": slug,
                }

                # Find the employee record for the user
                try:
                    employee = Employee.objects.get(user=user)
                except Employee.DoesNotExist:
                    return Response(
                        {"error": True, "detail": "User is not associated with any employee record"},
                        status=status.HTTP_403_FORBIDDEN,
                    )

                # Get the list of companies the employee is associated with
                companies = Company.objects.filter(outlets__outletaccess__employee=employee).distinct()
                user_details["companies"] = []

                for company in companies:
                    # Get the outlets the employee has access to within this company
                    outlets_access = OutletAccess.objects.filter(employee=employee, outlet__company=company)
                    outlets = [
                        {
                            "id": outlet_access.outlet.id,
                            "name": outlet_access.outlet.outlet_name,
                            "address": outlet_access.outlet.address,
                            "permissions": outlet_access.permissions,
                        }
                        for outlet_access in outlets_access
                    ]

                    # Add company and related outlets to the user details
                    user_details["companies"].append({
                        "id": company.id,
                        "name": company.name,
                        "address": company.address,
                        "number_of_outlets": company.number_of_outlets,  # Count outlets for the company
                        "number_of_employees": Employee.objects.filter(company=company).count(),  # Count employees for the company
                        "outlets": outlets,  # Outlets the employee has access to
                    })

                return Response(
                    {
                        "error": False,
                        "detail": "User logged in successfully",
                        "token": token.key,
                        "user_details": user_details,
                    },
                    status=status.HTTP_200_OK,
                )

            return Response(
                {"error": True, "detail": "Invalid username or password "},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        return Response(
            {"error": True, "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )







@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "error": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "details": openapi.Schema(type=openapi.TYPE_STRING),
                "categories": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                ),
            },
        ),
        500: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "error": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "details": openapi.Schema(type=openapi.TYPE_STRING),
                "categories": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                ),
            },
        ),
    },
)
@api_view(['GET'])
@permission_classes([AllowAny])
def category_list(request):
    try:
        category_names = Category.objects.values_list('name', flat=True)
        return Response({
            "error": False,
            "details": "Categories fetched successfully",
            "categories": list(category_names),
        })
    except Exception as e:
        return Response({
            "error": True,
            "details": f"An error occurred: {str(e)}"
        })









@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response(
            description='Products fetched successfully',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    "details": openapi.Schema(type=openapi.TYPE_STRING),
                    "products": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "name": openapi.Schema(type=openapi.TYPE_STRING),
                                "price": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "description": openapi.Schema(type=openapi.TYPE_STRING),
                                "gst_percentage": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "is_gst_inclusive": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                "created_at": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                "updated_at": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                "category": openapi.Schema(type=openapi.TYPE_STRING),
                                "variants": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                            "name": openapi.Schema(type=openapi.TYPE_STRING),
                                            "price": openapi.Schema(type=openapi.TYPE_NUMBER),
                                            "is_gst_inclusive": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                            "extra_description": openapi.Schema(type=openapi.TYPE_STRING),
                                            "created_at": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                            "updated_at": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                        }
                                    )
                                ),
                                "image_url": openapi.Schema(type=openapi.TYPE_STRING, description="Absolute URL of the product image")
                            }
                        )
                    ),
                }
            )
        ),
        500: openapi.Response(
            description='Internal Server Error',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    "details": openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def product_list(request):
    try:
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response({
            "error": False,
            "details": "Products fetched successfully",
            "products": serializer.data
        })
    except Exception as e:
        return Response({
            "error": True,
            "details": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        
        






# {
#   "customer": {
#     "name": "John Doe",
#     "phone_number": "1234567890"
#   },
#   "items": [
#     {
#       "product": 1,
#       "quantity": 2
#     },
#     {
#       "product_variant": 5,
#       "quantity": 1
#     }
#   ],
#   "address": "123, Main Street, City, State, ZIP",
#   "mode": "cash"
# }
def generate_order_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

@swagger_auto_schema(
    method='post',
    request_body=OrderSerializer,
    responses={
        201: openapi.Response(
            description="Order placed successfully",
            schema=OrderSerializer
        ),
        400: openapi.Response(
            description="Invalid request data"
        ),
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def place_order(request, outlet_id):
    try:
        data = request.data
        customer_data = data.get('customer')
        items_data = data.get('items')

        # Create the Order
        order = Order.objects.create(
            outlet_id=outlet_id,
            order_number=generate_order_number(),
            total_price=Decimal('0.00'),
            gst=Decimal('0.00'),
            status='PENDING',
            order_date=timezone.now(),
            address=data.get('address', ''),
            mode=data.get('mode', ''),
        )

        total_price = Decimal('0.00')
        total_gst = Decimal('0.00')

        # Process each order item
        for item_data in items_data:
            product_id = item_data.get('product')
            variant_id = item_data.get('product_variant')
            quantity = item_data.get('quantity')

            if product_id:
                product = Product.objects.get(id=product_id)
                price = product.price
                gst = product.gst_percentage
                is_gst_inclusive = product.is_gst_inclusive
            elif variant_id:
                variant = ProductVariant.objects.get(id=variant_id)
                product = variant.product
                price = variant.price
                gst = product.gst_percentage
                is_gst_inclusive = product.is_gst_inclusive
            else:
                return Response({
                    "error": True,
                    "details": "Either product or variant ID must be provided"
                }, status=status.HTTP_400_BAD_REQUEST)

            total_item_price = price * quantity
            gst_amount = (gst / Decimal('100')) * total_item_price
            total_item_gst_inclusive = total_item_price + gst_amount if not is_gst_inclusive else total_item_price

            # Create OrderItem
            OrderItem.objects.create(
                order=order,
                product=product if product_id else None,
                product_variant=variant if variant_id else None,
                quantity=quantity,
                price=price,
                total_price=total_item_gst_inclusive,
                gst=gst_amount
            )

            total_price += total_item_gst_inclusive
            total_gst += gst_amount

        # Update the total price and GST of the order
        order.total_price = total_price
        order.gst = total_gst
        order.save()

        # Create Customer
        customer_serializer = CustomerSerializer(data=customer_data)
        if customer_serializer.is_valid():
            customer = customer_serializer.save(order=order)
        else:
            return Response({
                "error": True,
                "details": "Invalid customer data"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Serialize and return the created order
        order_serializer = OrderSerializer(order)
        return Response(order_serializer.data, status=status.HTTP_201_CREATED)

    except Product.DoesNotExist:
        return Response({
            "error": True,
            "details": "Product not found"
        }, status=status.HTTP_400_BAD_REQUEST)
    except ProductVariant.DoesNotExist:
        return Response({
            "error": True,
            "details": "Product variant not found"
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            "error": True,
            "details": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)









@api_view(['GET'])
@permission_classes([AllowAny])
def orders_past_three_hours(request, outlet_id):
    try:
        # Calculate the time 3 hours ago from now
        three_hours_ago = timezone.now() - timedelta(hours=3)

        # Filter orders for the specific outlet and within the past three hours
        orders = Order.objects.filter(
            outlet_id=outlet_id,
            order_date__gte=three_hours_ago
        ).order_by('-order_date')

        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 10  # You can adjust the page size as needed
        result_page = paginator.paginate_queryset(orders, request)

        # Prepare the response data
        total_orders = orders.count()
        total_pages = paginator.page.paginator.num_pages
        current_page = paginator.page.number
        orders_on_current_page = len(result_page)

        # Custom metadata to include in the response
        response_data = {
            "error": False,
            "details": "Orders fetched successfully",
            "current_page": current_page,
            "total_orders": total_orders,
            "orders_on_current_page": orders_on_current_page,
            "total_pages": total_pages,
            "orders": [
                {
                    "order_number": order.order_number,
                    "order_date": order.order_date,
                    "total_price": str(order.total_price),
                    "status": order.status,
                    "mode": order.mode,
                }
                for order in result_page
            ]
        }

        return paginator.get_paginated_response(response_data)
    except Exception as e:
        return Response({
            "error": True,
            "details": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)










@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('order_number', openapi.IN_QUERY, description="Order number to fetch the details of the order", type=openapi.TYPE_STRING)
    ],
    responses={
        200: openapi.Response(
            description="Order fetched successfully",
            schema=OrderSerializer
        ),
        400: openapi.Response(
            description="Bad Request, missing order number",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'details': openapi.Schema(type=openapi.TYPE_STRING),
                }
            ),
        ),
        404: openapi.Response(
            description="Order not found",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'details': openapi.Schema(type=openapi.TYPE_STRING),
                }
            ),
        ),
        500: openapi.Response(
            description="Internal server error",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'details': openapi.Schema(type=openapi.TYPE_STRING),
                }
            ),
        ),
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def order_details(request, outlet_id):
    order_number = request.query_params.get('order_number')

    if not order_number:
        return Response({
            "error": True,
            "details": "Order number is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get the order based on outlet_id and order_number
        order = Order.objects.filter(outlet_id=outlet_id, order_number=order_number).first()

        if not order:
            return Response({
                "error": True,
                "details": "Order not found"
            }, status=status.HTTP_404_NOT_FOUND)

        # Serialize the order along with the related items and customer
        serializer = OrderListSerializer(order)

        return Response({
            "error": False,
            "details": "Order fetched successfully",
            "order": serializer.data
        })

    except Exception as e:
        return Response({
            "error": True,
            "details": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)










@swagger_auto_schema(
    method='post',
    request_body=StockRequestSerializer,
    responses={
        201: 'Stock request created successfully',
        400: 'Invalid data'
    }
)
@api_view(['POST'])
def create_stock_request(request, outlet_id):
    try:
        # Ensure outlet exists
        outlet = Outlet.objects.get(id=outlet_id)

        # Set the default status to 'PENDING'
        request.data['status'] = 'PENDING'
        request.data['outlet'] = outlet.id  # Automatically add outlet to request data

        # Serialize and create stock request
        serializer = StockRequestSerializer(data=request.data)
        if serializer.is_valid():
            stock_request = serializer.save()
            return Response({
                "error": False,
                "details": "Stock request created successfully",
                "stock_request": serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "error": True,
                "details": "Invalid data",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Outlet.DoesNotExist:
        return Response({
            "error": True,
            "details": f"Outlet with ID {outlet_id} not found"
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({
            "error": True,
            "details": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







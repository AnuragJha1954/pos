import random
import string

from decimal import Decimal

from django.template.loader import render_to_string
from django.forms.models import model_to_dict
from django.utils.dateformat import format as date_format

from django.shortcuts import render
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.timezone import localtime
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

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
    Employee,
    PlanAssignment,
    Plan
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
            print(request.data)
            print(serializer.is_valid())
            if serializer.is_valid():
                user = serializer.validated_data["user"]
                # role = serializer.validated_data["role"]
                # print(user)
                # print(role)
                token, _ = Token.objects.get_or_create(user=user)

                # Fetch the employee record for the user and role
                employee = Employee.objects.get(user=user)

                # Prepare user details
                user_details = {
                    "id": employee.user.id,
                    "username": employee.user.username,
                    "name": f"{employee.first_name} {employee.last_name}",
                    "email": employee.email,
                    "phone_number": employee.phone_number,
                    "address": employee.address,
                    "date_of_birth": employee.date_of_birth,
                    "profile_image": employee.profile_image.url if employee.profile_image else None,
                    "role": employee.get_role_display(),
                    "is_active": employee.is_active,
                    "employee_code": employee.employee_code,
                }

                # Fetch company details
                company = employee.company
                company_details = {
                    "id": company.id,
                    "name": company.name,
                    "address": company.address,
                    "gst_in": company.gst_in,
                    "number_of_outlets": company.number_of_outlets,
                    "number_of_employees": company.number_of_employees,
                }

                # Fetch outlet details for the employee
                outlets = Outlet.objects.filter(outletaccess__employee=employee).distinct()
                outlet_details = [
                    {
                        "id": outlet.id,
                        "name": outlet.outlet_name,
                        "logo": request.build_absolute_uri(outlet.logo.url) if outlet.logo else None,
                        "gst_number": outlet.gst_number,
                        "address": outlet.address,
                        "phone_number": outlet.phone_number,
                        "opening_hours": outlet.opening_hours,
                        "is_active": outlet.is_active,
                        "bank_account_number": outlet.bank_account_number,
                        "ifsc_code": outlet.ifsc_code,
                        "created_at": outlet.created_at,
                        "updated_at": outlet.updated_at,
                    }
                    for outlet in outlets
                ]

                # Fetch active plan details for the user
                from datetime import date
                plan_assignments = PlanAssignment.objects.filter(
                    user=user, status="active", valid_till__gte=date.today()
                )
                plans = [
                    {
                        "id": plan_assignment.plan.id,
                        "name": plan_assignment.plan.plan_name,
                        "price": str(plan_assignment.plan.plan_price),
                        "price_tenure": plan_assignment.plan.price_tenure,
                        "valid_till": plan_assignment.valid_till,
                        "status": plan_assignment.status,
                    }
                    for plan_assignment in plan_assignments
                ]

                # Prepare the response
                response_data = {
                    "error": False,
                    "detail": "User logged in successfully",
                    "token": token.key,
                    "user_details": user_details,
                    "company_details": company_details,
                    "outlet_details": outlet_details,
                    "plans": plans,
                }

                return Response(response_data, status=status.HTTP_200_OK)

            return Response(
                {"error": True, "detail": "Invalid username or password."},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        return Response(
            {"error": True, "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )








@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'outlet_id',
            openapi.IN_PATH,
            description="ID of the outlet for which categories are being fetched",
            type=openapi.TYPE_INTEGER,
            required=True,
        )
    ],
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "error": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Indicates if the request was successful"),
                "details": openapi.Schema(type=openapi.TYPE_STRING, description="Details about the response"),
                "categories": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="List of category names for the specified outlet",
                ),
            },
        ),
        404: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "error": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Indicates if the request failed"),
                "details": openapi.Schema(type=openapi.TYPE_STRING, description="Error details, e.g., 'Not Found'"),
            },
        ),
        500: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "error": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Indicates if an internal server error occurred"),
                "details": openapi.Schema(type=openapi.TYPE_STRING, description="Details about the server error"),
            },
        ),
    },
)
@api_view(['GET'])
@permission_classes([AllowAny])
def category_list(request, outlet_id):
    try:
        # Fetch the outlet to ensure it exists
        outlet = get_object_or_404(Outlet, id=outlet_id)

        # Fetch category names for the specified outlet
        category_names = Category.objects.filter(outlet=outlet).values_list('name', flat=True)

        return Response({
            "error": False,
            "details": "Categories fetched successfully",
            "categories": list(category_names),
        }, status=200)
    except Exception as e:
        return Response({
            "error": True,
            "details": f"An error occurred: {str(e)}"
        }, status=500)








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
        # Retrieve all products
        products = Product.objects.select_related('category').prefetch_related('variants').all()

        # Group products by category
        category_dict = {}
        for product in products:
            category_id = product.category.id
            category_name = product.category.name

            # Initialize the category in the dictionary if not already present
            if category_id not in category_dict:
                category_dict[category_id] = {
                    "category_id": category_id,
                    "category_name": category_name,
                    "items": []
                }

            # Serialize the product and append it to the category's items
            product_data = ProductSerializer(product).data
            category_dict[category_id]["items"].append(product_data)

        # Convert the dictionary to a list
        response_data = list(category_dict.values())

        return Response({
            "error": False,
            "details": "Products fetched successfully",
            "categories": response_data
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

        # Check if the customer exists
        customer = Customer.objects.filter(
            name=customer_data.get('name'),
            phone_number=customer_data.get('phone_number')
        ).first()

        if not customer:
            # Create a new customer if it doesn't exist
            customer = Customer.objects.create(
                name=customer_data.get('name'),
                phone_number=customer_data.get('phone_number')
            )

        # Create the Order
        order = Order.objects.create(
            outlet_id=outlet_id,
            order_number=generate_order_number(),
            total_price=Decimal('0.00'),
            gst=Decimal('0.00'),
            status='PENDING',
            order_date=localtime(timezone.now()),
            address=data.get('address', ''),
            mode=data.get('mode', ''),
        )

        # Link the customer to the order
        customer.order = order
        customer.save()

        total_price = Decimal('0.00')
        total_gst = Decimal('0.00')
        processed_items = []

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
                return JsonResponse({
                    "error": True,
                    "details": "Either product or variant ID must be provided"
                }, status=400)

            total_item_price = price * quantity

            if is_gst_inclusive:
                # GST-inclusive price logic
                rate_excluding_gst = price / (1 + gst / Decimal('100'))
                gst_amount = total_item_price - (rate_excluding_gst * quantity)
                amount_excluding_gst = total_item_price - gst_amount
            else:
                # GST-exclusive price logic
                gst_amount = (gst / Decimal('100')) * total_item_price
                rate_excluding_gst = price
                amount_excluding_gst = total_item_price

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

            # Add calculated data to processed items for context
            processed_items.append({
                "product_name": product.name,
                "variant_name": variant.name if variant_id else None,
                "quantity": quantity,
                "price": round(rate_excluding_gst, 2),  # Rate excl. GST
                "total_price": round(amount_excluding_gst, 2),  # Amount excl. GST
                "gst": round(gst_amount, 2),
            })

            total_price += total_item_gst_inclusive
            total_gst += gst_amount

        # Update the total price and GST of the order
        subtotal = total_price - total_gst  # Calculate subtotal before GST
        order.total_price = total_price
        order.gst = total_gst
        order.save()

        # Calculate CGST and SGST
        cgst = total_gst / 2
        sgst = total_gst / 2

        # Serialize and return the created order with customer details
        order_serializer = OrderSerializer(order, context={'request': request})
        response_data = order_serializer.data

        response_data['subtotal'] = round(subtotal, 2)
        
        # print(localtime(timezone.now()))
        # Format the order date
        formatted_date = order.order_date.strftime("%d-%m-%Y %I:%M %p")
        response_data['formatted_date'] = formatted_date

        # Add customer data and processed items to the response manually
        response_data['customer'] = {
            "name": customer.name,
            "phone_number": customer.phone_number
        }
        response_data['items'] = processed_items

        # Add CGST and SGST to the response
        response_data['cgst'] = round(cgst, 2)
        response_data['sgst'] = round(sgst, 2)

        # Pass the response data directly to the bill.html template
        return render(request, "bill.html", response_data)

    except Product.DoesNotExist:
        return JsonResponse({
            "error": True,
            "details": "Product not found"
        }, status=400)
    except ProductVariant.DoesNotExist:
        return JsonResponse({
            "error": True,
            "details": "Product variant not found"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "error": True,
            "details": f"An error occurred: {str(e)}"
        }, status=500)
















@api_view(['POST'])
@permission_classes([AllowAny])
def print_kot(request, outlet_id):
    # Fetch the outlet using the outlet ID
    outlet = get_object_or_404(Outlet, id=outlet_id)
    
    # Get the latest order for the outlet
    latest_order = outlet.orders.order_by('-order_date').first()
    
    if not latest_order:
        return render(request, "kot.html", {"error": "No orders found for this outlet."})

    # Get the order items
    items = latest_order.items.all()

    # Prepare the context for the template
    context = {
        "order_number": latest_order.order_number,
        "order_date": date_format(latest_order.order_date, "Y-m-d H:i"),
        "items": [
            {
                "product_name": item.product.name if item.product else None,
                "variant_name": item.product_variant.name if item.product_variant else None,
                "quantity": item.quantity,
            }
            for item in items
        ],
    }

    # Render the template with the context
    return render(request, "kot.html", context)

















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
            "next_page_url": paginator.get_next_link(),
            "previous_page_url": paginator.get_previous_link(),
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

        return Response(response_data, status=status.HTTP_200_OK)
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

        # Get the customer associated with the order
        customer = order.customers.first()  # Assuming an Order has a related Customer

        # Serialize the order and its items
        items = [
            {
                "product_name": item.product.name if item.product else None,
                "product_variant_name": item.product_variant.name if item.product_variant else None,
                "quantity": item.quantity,
                "price": str(item.price),
                "total_price": str(item.total_price),
                "gst": str(item.gst),
            }
            for item in order.items.all()
        ]

        # Prepare customer details
        customer_details = {
            "name": customer.name if customer else None,
            "phone_number": customer.phone_number if customer else None,
        }

        # Build the response data
        response_data = {
            "error": False,
            "details": "Order fetched successfully",
            "order": {
                "order_number": order.order_number,
                "order_date": order.order_date,
                "total_price": str(order.total_price),
                "gst": str(order.gst),
                "status": order.status,
                "mode": order.mode,
                "address": order.address,
                "items": items,
                "customer": customer_details,
            },
        }

        return Response(response_data, status=status.HTTP_200_OK)

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
@permission_classes([AllowAny])
def create_stock_request(request, outlet_id):
    try:
        # Ensure outlet exists
        outlet = Outlet.objects.get(id=outlet_id)

        # Set the default status to 'PENDING' and add outlet ID to request data
        request.data['status'] = 'PENDING'
        request.data['outlet'] = outlet.id

        # Check if products and/or variants are provided
        products = request.data.get('products')  # Expecting a list of product IDs
        variants = request.data.get('variants')  # Expecting a list of variant IDs

        if not products and not variants:
            return Response({
                "error": True,
                "details": "At least one product or product variant must be provided."
            }, status=status.HTTP_400_BAD_REQUEST)

        stock_requests = []
        if products:
            for product_id in products:
                stock_request = StockRequest(
                    product_id=product_id,
                    outlet=outlet
                )
                stock_requests.append(stock_request)

        if variants:
            for variant_id in variants:
                stock_request = StockRequest(
                    product_variant_id=variant_id,
                    outlet=outlet
                )
                stock_requests.append(stock_request)

        if stock_requests:
            StockRequest.objects.bulk_create(stock_requests)
            serializer = StockRequestSerializer(stock_requests, many=True)
            return Response({
                "error": False,
                "details": "Stock requests created successfully",
                "stock_requests": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "error": True,
            "details": "Failed to create stock requests"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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









import random
import string
import requests 

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
from django.conf import settings

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from firebase_admin import messaging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination

from datetime import timedelta,datetime

from .serializers import ( 
    CustomUserCounterLoginSerializer,
    ProductSerializer,
    OrderItemSerializer,
    OrderSerializer,
    CustomerSerializer,
    OrderListSerializer,
    OrderItemListSerializer,
    CustomerListSerializer,
    StockRequestSerializer,
    TableSerializer,
    TableOrderSerializer,
    ExpenseSerializer,
    
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
    Plan,
    FCMToken,
    Table,
    Expense,
    KOT,
    OrderPayment,
    KOTDevice,
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
            # print(request.data)
            # print(serializer.is_valid())
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
                outlet_count = outlets.count()
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
                    "outlet_count": outlet_count,
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
def product_list(request, outlet_id):
    try:
        # Get the search query parameter
        search_query = request.GET.get('product')
        
        # Retrieve all products base queryset
        base_products = Product.objects.filter(outlet_id=outlet_id).select_related('category').prefetch_related('variants').all()
        
        # Apply search filter if provided
        if search_query:
            base_products = base_products.filter(name__icontains=search_query)
        
        # Separate in-stock and stock-out products
        in_stock_products = base_products.filter(is_stock_out=False)
        stock_out_products = base_products.filter(is_stock_out=True)
        
        # Function to group products by category
        def group_by_category(products_queryset):
            category_dict = {}
            for product in products_queryset:
                category_id = product.category.id
                category_name = product.category.name

                if category_id not in category_dict:
                    category_dict[category_id] = {
                        "category_id": category_id,
                        "category_name": category_name,
                        "items": []
                    }

                product_data = ProductSerializer(product).data

                # Rename keys and structure to match frontend format
                formatted_product = {
                    "id": product_data["id"],
                    "name": product_data["name"],
                    "price": product_data.get("price"),
                    "description": product_data.get("description"),
                    "gst_percent": product_data.get("gst_percentage"),  # renamed key
                    "is_gst_inclusive": product_data.get("is_gst_inclusive"),
                    "created_at": product_data.get("created_at"),
                    "updated_at": product_data.get("updated_at"),
                    "category_id": category_id,
                    "category_name": category_name,
                    "image_url": product_data.get("image_url"),
                    "is_veg": product_data.get("is_veg"),
                    "is_stock_out": product_data.get("is_stock_out"),
                    "variants": [
                        {
                            "id": v["id"],
                            "name": v["name"],
                            "price": v["price"],
                            "is_gst_inclusive": v["is_gst_inclusive"],
                            "extra_description": v.get("extra_description", []),
                            "created_at": v.get("created_at"),
                            "updated_at": v.get("updated_at"),
                            "is_stock_out": v.get("is_stock_out")
                        }
                        for v in product_data.get("variants", [])
                    ],
                }

                category_dict[category_id]["items"].append(formatted_product)
            return list(category_dict.values())

        # Build final response matching frontend requirement
        response_data = {
            "error": False,
            "message": "Products fetched successfully",  # renamed from 'details'
            "products": group_by_category(in_stock_products),  # renamed from 'categories'
            "stock_out_categories": group_by_category(stock_out_products)
        }

        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            "error": True,
            "message": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# def product_list(request,outlet_id):
#     try:
#         # Get the search query parameter
#         search_query = request.GET.get('product')
        
#         # Retrieve all products base query set
#         base_products = Product.objects.filter(outlet_id=outlet_id).select_related('category').prefetch_related('variants').all()
        
#         # Apply search filter if search query is provided
#         if search_query:
#             base_products = base_products.filter(name__icontains=search_query)
        
        
#         # Separate in-stock and stock-out products
#         in_stock_products = base_products.filter(is_stock_out=False)
#         stock_out_products = base_products.filter(is_stock_out=True)
        
#         # Function to group products by category
#         def group_by_category(products_queryset):
#             category_dict = {}
#             for product in products_queryset:
#                 category_id = product.category.id
#                 category_name = product.category.name
#                 if category_id not in category_dict:
#                     category_dict[category_id] = {
#                         "category_id": category_id,
#                         "category_name": category_name,
#                         "items": []
#                     }
#                 product_data = ProductSerializer(product).data
#                 category_dict[category_id]["items"].append(product_data)
#             return list(category_dict.values())

#         # # Group products by category
#         # category_dict = {}
#         # for product in products:
#         #     category_id = product.category.id
#         #     category_name = product.category.name

#         #     # Initialize the category in the dictionary if not already present
#         #     if category_id not in category_dict:
#         #         category_dict[category_id] = {
#         #             "category_id": category_id,
#         #             "category_name": category_name,
#         #             "items": []
#         #         }

#         #     # Serialize the product and append it to the category's items
#         #     product_data = ProductSerializer(product).data
#         #     category_dict[category_id]["items"].append(product_data)

#         response_data = {
#             "error": False,
#             "details": "Products fetched successfully",
#             "categories": group_by_category(in_stock_products),
#             "stock_out_categories": group_by_category(stock_out_products),
#         }
         
#         return Response(response_data, status=status.HTTP_200_OK)
        
#         # # Convert the dictionary to a list
#         # response_data = list(category_dict.values())

#         # return Response({
#         #     "error": False,
#         #     "details": "Products fetched successfully",
#         #     "categories": response_data
#         # })
#     except Exception as e:
#         return Response({
#             "error": True,
#             "details": f"An error occurred: {str(e)}"
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        
        


def send_order_notification(registration_token):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title="Order Received",
                body="New Order Alert",
            ),
            token=registration_token,
        )

        response = messaging.send(message)
        return {
            "error": False,
            "detail": "Message sent successfully and response from firebase is"+ response
        }

    except Exception as e:
        return {
            "error": True,
            "detail": str(e)
        }


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

# 🔥 KOT ACCESS CHECK
def has_kot_access(user):
    plan = PlanAssignment.objects.filter(
        user=user,
        status='active'
    ).select_related('plan').first()

    return plan.plan.has_kot if plan else False


def generate_order_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

place_order_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['customer', 'items'],
    properties={
        'table_id': openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Required for dine-in orders"
        ),

        'is_draft': openapi.Schema(
            type=openapi.TYPE_BOOLEAN,
            description="Set true to save as draft"
        ),

        'payment_mode': openapi.Schema(
            type=openapi.TYPE_STRING,
            enum=['upi', 'cash', 'coupon'],
            description="Required for takeaway orders"
        ),

        'upi_type': openapi.Schema(
            type=openapi.TYPE_STRING,
            enum=['gpay', 'phonepe', 'paytm'],
            description="Required only if payment_mode = upi"
        ),

        'amount': openapi.Schema(
            type=openapi.TYPE_NUMBER,
            format='decimal',
            description="Paid amount (optional, defaults to total)"
        ),

        'customer': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'phone_number'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),

        'items': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Items(
                type=openapi.TYPE_OBJECT,
                required=['quantity'],
                properties={
                    'product': openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        description="Product ID (either product OR variant required)"
                    ),
                    'product_variant': openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        description="Variant ID"
                    ),
                    'quantity': openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        minimum=1
                    ),
                }
            )
        ),
    }
)

@swagger_auto_schema(
    method='post',
    operation_description="""
Place Order API

### Order Types:
- 🧾 Draft → No processing
- 🍽️ Dine-in → Sent to KOT, pay later
- 🛍️ Takeaway → Payment required immediately

### Payment Modes (Takeaway Only):
- UPI (requires upi_type)
- Cash
- Coupon
""",
    request_body=place_order_request_schema,
    responses={
        200: openapi.Response(
            description="Order created successfully",
            examples={
                "application/json": {
                    "error": False,
                    "data": {
                        "order_id": 1,
                        "order_number": "AB12CD34",
                        "status": "settled",
                        "payment_status": "success",
                        "total_price": 500,
                        "gst": 50,
                        "customer": {
                            "name": "Anurag",
                            "phone_number": "9999999999"
                        },
                        "table": None,
                        "items": [
                            {
                                "product_name": "Burger",
                                "variant_name": None,
                                "quantity": 2,
                                "price": 200,
                                "gst": 20
                            }
                        ]
                    },
                    "payment": {
                        "required": True,
                        "mode": "upi",
                        "upi_type": "gpay",
                        "status": "success"
                    }
                }
            }
        ),

        400: openapi.Response(
            description="Invalid request (e.g., missing payment_mode for takeaway)"
        ),

        500: openapi.Response(
            description="Internal server error"
        )
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def place_order(request, outlet_id):
    try:
        data = request.data

        customer_data = data.get("customer")
        items_data = data.get("items")
        table_id = data.get("table_id")
        is_draft = data.get("is_draft", False)

        payment_mode = data.get("payment_mode")
        upi_type = data.get("upi_type")
        paid_amount = Decimal(str(data.get("amount", "0")))

        order_number = generate_order_number()

        # Customer
        customer, _ = Customer.objects.get_or_create(
            name=customer_data.get("name"),
            phone_number=customer_data.get("phone_number")
        )

        is_takeaway = not bool(table_id)
        # kot_enabled = has_kot_access(request.user)

        # 🔥 STATUS DECISION
        if is_draft:
            order_status = "draft"
            payment_required = False

        elif is_takeaway:
            order_status = "payment_pending"
            payment_required = True

        else:
            order_status = "pending"
            payment_required = False

        # Create Order
        order = Order.objects.create(
            outlet_id=outlet_id,
            order_number=order_number,
            total_price=Decimal("0.00"),
            gst=Decimal("0.00"),
            status=order_status,
            payment_status="pending"
        )

        customer.order = order
        customer.save()

        # Table handling
        table = None
        if table_id:
            table = Table.objects.get(id=table_id)
            table.current_order = order
            table.status = "running"
            table.save()

            order.table_number = table
            order.save()

        total_price = Decimal("0.00")
        total_gst = Decimal("0.00")
        processed_items = []

        # 🔥 ITEM PROCESSING
        for item_data in items_data:
            product_id = item_data.get("product")
            variant_id = item_data.get("product_variant")
            quantity = item_data.get("quantity")

            if product_id:
                product = Product.objects.get(id=product_id)
                price = product.price
                gst = product.gst_percentage or Decimal("0.00")
                is_gst_inclusive = product.is_gst_inclusive
                variant = None
            else:
                variant = ProductVariant.objects.get(id=variant_id)
                product = variant.product
                price = variant.price
                gst = product.gst_percentage or Decimal("0.00")
                is_gst_inclusive = product.is_gst_inclusive

            total_item_price = price * quantity

            if is_gst_inclusive:
                rate_excl = price / (1 + gst / Decimal("100"))
                gst_amount = total_item_price - (rate_excl * quantity)
            else:
                gst_amount = (gst / Decimal("100")) * total_item_price

            final_price = (
                total_item_price if is_gst_inclusive else total_item_price + gst_amount
            )

            # Item status
            item_status = "pending"

            OrderItem.objects.create(
                order=order,
                product=product if product_id else None,
                product_variant=variant,
                quantity=quantity,
                price=price,
                total_price=final_price,
                gst=gst_amount,
                status=item_status
            )

            processed_items.append({
                "product_name": product.name,
                "variant_name": variant.name if variant else None,
                "quantity": quantity,
                "price": round(price, 2),
                "gst": round(gst_amount, 2),
            })

            total_price += final_price
            total_gst += gst_amount

        # Update totals
        order.total_price = total_price
        order.gst = total_gst

        # 🔥 PAYMENT HANDLING (NEW CLEAN FLOW)
        if payment_required:
            order.mode = payment_mode
            order.upi_type = upi_type

            if payment_mode in ["upi", "cash", "coupon"]:
                order.payment_status = "success"
                order.status = "settled"
            else:
                order.payment_status = "pending"

        else:
            order.payment_status = "not_required"

        order.save()

        # Response
        return JsonResponse({
            "error": False,
            "data": {
                "order_id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "payment_status": order.payment_status,
                "total_price": float(total_price),
                "gst": float(total_gst),
                "customer": customer.name,
                "table": table.table_number if table else None,
                "items": processed_items,
            }
        })

    except Exception as e:
        return JsonResponse(
            {"error": True, "details": str(e)},
            status=500
        )








# def place_order(request, outlet_id):
#     try:
#         data = request.data

#         customer_data = data.get("customer")
#         items_data = data.get("items")
#         table_id = data.get("table_id")
#         is_draft = data.get("is_draft", False)

#         # 🔥 AUTO ORDER NUMBER
#         order_number = generate_order_number()

#         # Customer
#         customer, _ = Customer.objects.get_or_create(
#             name=customer_data.get("name"),
#             phone_number=customer_data.get("phone_number")
#         )

#         is_takeaway = not bool(table_id)
#         kot_enabled = has_kot_access(request.user)

#         # 🔥 STATUS DECISION
#         if is_draft:
#             order_status = "draft"
#             payment_required = False

#         elif is_takeaway:
#             # 🔥 Takeaway → payment first
#             order_status = "payment_pending"
#             payment_required = True

#         else:
#             # 🔥 Dine-in + send to KOT
#             order_status = "pending"   # goes to KOT
#             payment_required = False

#         # Create Order
#         order = Order.objects.create(
#             outlet_id=outlet_id,
#             order_number=order_number,
#             total_price=Decimal("0.00"),
#             gst=Decimal("0.00"),
#             status=order_status,
#             order_date=localtime(timezone.now()),
#             payment_status="pending"
#         )

#         customer.order = order
#         customer.save()

#         # Table Handling
#         table = None
#         if table_id:
#             table = Table.objects.get(id=table_id)
#             table.current_order = order
#             table.status = "running"
#             table.save()

#             order.table = table
#             order.save()

#         total_price = Decimal("0.00")
#         total_gst = Decimal("0.00")
#         processed_items = []

#         # Items Processing
#         for item_data in items_data:
#             product_id = item_data.get("product")
#             variant_id = item_data.get("product_variant")
#             quantity = item_data.get("quantity")

#             if product_id:
#                 product = Product.objects.get(id=product_id)
#                 price = product.price
#                 gst = product.gst_percentage or Decimal("0.00")
#                 is_gst_inclusive = product.is_gst_inclusive
#                 variant = None
#             else:
#                 variant = ProductVariant.objects.get(id=variant_id)
#                 product = variant.product
#                 price = variant.price
#                 gst = product.gst_percentage or Decimal("0.00")
#                 is_gst_inclusive = product.is_gst_inclusive

#             total_item_price = price * quantity

#             if is_gst_inclusive:
#                 rate_excl = price / (1 + gst / Decimal("100"))
#                 gst_amount = total_item_price - (rate_excl * quantity)
#             else:
#                 gst_amount = (gst / Decimal("100")) * total_item_price

#             total_item_price_final = (
#                 total_item_price if is_gst_inclusive else total_item_price + gst_amount
#             )
            
#             # 🔥 Item status logic
#             if is_draft:
#                 item_status = "pending"
#             elif is_takeaway:
#                 item_status = "pending"   # will process after payment
#             else:
#                 item_status = "pending"   # goes to KOT

#             OrderItem.objects.create(
#                 order=order,
#                 product=product if product_id else None,
#                 product_variant=variant,
#                 quantity=quantity,
#                 price=price,
#                 total_price=total_item_price_final,
#                 gst=gst_amount,
#                 status = item_status
                
#             )

#             processed_items.append({
#                 "product_name": product.name,
#                 "variant_name": variant.name if variant else None,
#                 "quantity": quantity,
#                 "price": round(price, 2),
#                 "gst": round(gst_amount, 2),
#             })

#             total_price += total_item_price_final
#             total_gst += gst_amount

#         # Update order totals
#         order.total_price = total_price
#         order.gst = total_gst
#         order.save()

#         cgst = total_gst / 2
#         sgst = total_gst / 2
#         subtotal = total_price - total_gst

#         # 🔥 PINELABS INTEGRATION (ADDED)
#         if payment_required:
#             payload = {
#                 "TransactionNumber": order.order_number,
#                 "SequenceNumber": 1,
#                 "AllowedPaymentMode": "1|10",
#                 "Amount": int(total_price * 100),
#                 "UserID": "SYSTEM",
#                 "MerchantID": settings.PINELABS_MERCHANT_ID,
#                 "SecurityToken": settings.PINELABS_SECURITY_TOKEN,
#                 "ClientId": settings.PINELABS_CLIENT_ID,
#                 "StoreId": settings.PINELABS_STORE_ID,
#                 "AutoCancelDurationInMinutes": settings.PINELABS_AUTO_CANCEL_MINUTES,
#                 "PaperPOSID": settings.PINELABS_TERMINAL_ID,
#                 "PaperPOSTxnOptionToDisplay": 2,
#                 "PaperPOSTxnIdentifier": 2,
#             }

#             res = requests.post(
#                 f"{settings.PINELABS_BASE_URL}/UploadBilledTransaction",
#                 json=payload
#             )

#             pine_response = res.json()

#             if pine_response.get("ResponseCode") == "0":
#                 order.plutus_transaction_reference_id = pine_response.get("PlutusTransactionReferenceID")
#                 order.payment_status = "initiated"
#                 order.pine_response = pine_response
#                 order.save()
#             else:
#                 order.payment_status = "failed"
#                 order.pine_response = pine_response
#                 order.save()

#                 return JsonResponse({
#                     "error": True,
#                     "details": "Payment initiation failed",
#                     "pine_response": pine_response
#                 }, status=400)
#         else:
#             order.payment_status = "not_required"
#             order.save()

#         # 🔥 ORIGINAL RESPONSE (UNCHANGED)
#         response_data = {
#             "order_id": order.id,
#             "order_number": order.order_number,
#             "status": order.status,
#             "total_price": round(total_price, 2),
#             "gst": round(total_gst, 2),
#             "cgst": round(cgst, 2),
#             "sgst": round(sgst, 2),
#             "subtotal": round(subtotal, 2),
#             "customer": {
#                 "name": customer.name,
#                 "phone_number": customer.phone_number,
#             },
#             "items": processed_items,
#             "table": table.table_number if table else None,
#             "formatted_date": order.order_date.strftime("%d-%m-%Y %I:%M %p"),
#             "kot_enabled": kot_enabled,
#         }

#         bill_html = render_to_string("bill.html", response_data)

#         return JsonResponse({
#             "error": False,
#             "data": response_data,
#             "bill_template": bill_html,

#             # 🔥 ONLY ADDITION (SAFE)
#             "payment": {
#                 "required": payment_required,
#                 "status": order.payment_status,
#                 "plutus_transaction_reference_id": order.plutus_transaction_reference_id,
#                 "transaction_number": order.order_number,
#             }
#         })

#     except Exception as e:
#         return JsonResponse(
#             {"error": True, "details": str(e)},
#             status=500
#         )









# def place_order(request, outlet_id, order_number):
#     try:
#         data = request.data

#         customer_data = data.get("customer")
#         items_data = data.get("items")
#         table_id = data.get("table_id")   # 👈 NEW
#         is_draft = data.get("is_draft", False)  # 👈 NEW

#         # Customer
#         customer, _ = Customer.objects.get_or_create(
#             name=customer_data.get("name"),
#             phone_number=customer_data.get("phone_number")
#         )

#         # 🔥 Determine order status
#         if table_id:
#             if is_draft:
#                 order_status = "draft"
#             else:
#                 order_status = "confirmed"
#         else:
#             order_status = "confirmed"  # takeaway

#         # Create Order
#         order = Order.objects.create(
#             outlet_id=outlet_id,
#             order_number=order_number,
#             total_price=Decimal("0.00"),
#             gst=Decimal("0.00"),
#             status=order_status,
#             order_date=localtime(timezone.now()),
#         )

#         customer.order = order
#         customer.save()

#         # 🔥 Table Handling
#         table = None
#         if table_id:
#             table = Table.objects.get(id=table_id)

#             table.current_order = order

#             # Draft → keep table empty
#             if is_draft:
#                 table.status = "running"
#             else:
#                 table.status = "running"

#             table.save()

#             order.table = table
#             order.save()

#         total_price = Decimal("0.00")
#         total_gst = Decimal("0.00")
#         processed_items = []

#         # 🔥 Items Processing
#         for item_data in items_data:
#             product_id = item_data.get("product")
#             variant_id = item_data.get("product_variant")
#             quantity = item_data.get("quantity")

#             if product_id:
#                 product = Product.objects.get(id=product_id)
#                 price = product.price
#                 gst = product.gst_percentage or Decimal("0.00")
#                 is_gst_inclusive = product.is_gst_inclusive
#                 variant = None
#             elif variant_id:
#                 variant = ProductVariant.objects.get(id=variant_id)
#                 product = variant.product
#                 price = variant.price
#                 gst = product.gst_percentage or Decimal("0.00")
#                 is_gst_inclusive = product.is_gst_inclusive
#             else:
#                 return JsonResponse(
#                     {"error": True, "details": "Product or variant required"},
#                     status=400
#                 )

#             total_item_price = price * quantity

#             if is_gst_inclusive:
#                 rate_excl_gst = price / (1 + gst / Decimal("100"))
#                 gst_amount = total_item_price - (rate_excl_gst * quantity)
#             else:
#                 gst_amount = (gst / Decimal("100")) * total_item_price

#             total_item_price_final = (
#                 total_item_price if is_gst_inclusive else total_item_price + gst_amount
#             )

#             OrderItem.objects.create(
#                 order=order,
#                 product=product if product_id else None,
#                 product_variant=variant,
#                 quantity=quantity,
#                 price=price,
#                 total_price=total_item_price_final,
#                 gst=gst_amount,
#                 status="processing"  # 👈 default
#             )

#             processed_items.append({
#                 "product_name": product.name,
#                 "variant_name": variant.name if variant else None,
#                 "quantity": quantity,
#                 "price": round(price, 2),
#                 "gst": round(gst_amount, 2),
#             })

#             total_price += total_item_price_final
#             total_gst += gst_amount

#         # Update order totals
#         order.total_price = total_price
#         order.gst = total_gst
#         order.save()

#         cgst = total_gst / 2
#         sgst = total_gst / 2
#         subtotal = total_price - total_gst

#         response_data = {
#             "order_id": order.id,
#             "order_number": order.order_number,
#             "status": order.status,
#             "total_price": round(total_price, 2),
#             "gst": round(total_gst, 2),
#             "cgst": round(cgst, 2),
#             "sgst": round(sgst, 2),
#             "subtotal": round(subtotal, 2),
#             "customer": {
#                 "name": customer.name,
#                 "phone_number": customer.phone_number,
#             },
#             "items": processed_items,
#             "table": table.table_number if table else None,
#             "formatted_date": order.order_date.strftime("%d-%m-%Y %I:%M %p"),
#         }

#         # 🔥 Render bill HTML as string
#         bill_html = render_to_string("bill.html", response_data)

#         return JsonResponse({
#             "error": False,
#             "data": response_data,
#             "bill_template": bill_html  # 👈 FULL HTML
#         })

#     except Exception as e:
#         return JsonResponse(
#             {"error": True, "details": str(e)},
#             status=500
#         )










# def place_order(request, outlet_id,order_number):
#     try:
#         data = request.data


#         customer_data = data.get("customer")
#         items_data = data.get("items")

#         # Customer lookup / create
#         customer, _ = Customer.objects.get_or_create(
#             name=customer_data.get("name"),
#             phone_number=customer_data.get("phone_number")
#         )

#         # ✅ Use existing order number
#         order = Order.objects.create(
#             outlet_id=outlet_id,
#             order_number=order_number,
#             total_price=Decimal("0.00"),
#             gst=Decimal("0.00"),
#             status="PENDING",
#             order_date=localtime(timezone.now()),
#             address=data.get("address", ""),
#             mode=data.get("mode", ""),
#         )

#         customer.order = order
#         customer.save()

#         total_price = Decimal("0.00")
#         total_gst = Decimal("0.00")
#         processed_items = []

#         for item_data in items_data:
#             product_id = item_data.get("product")
#             variant_id = item_data.get("product_variant")
#             quantity = item_data.get("quantity")

#             if product_id:
#                 product = Product.objects.get(id=product_id)
#                 price = product.price
#                 gst = product.gst_percentage
#                 is_gst_inclusive = product.is_gst_inclusive
#                 variant = None
#             elif variant_id:
#                 variant = ProductVariant.objects.get(id=variant_id)
#                 product = variant.product
#                 price = variant.price
#                 gst = product.gst_percentage
#                 is_gst_inclusive = product.is_gst_inclusive
#             else:
#                 return JsonResponse(
#                     {"error": True, "details": "Product or variant required"},
#                     status=400
#                 )

#             total_item_price = price * quantity

#             if is_gst_inclusive:
#                 rate_excl_gst = price / (1 + gst / Decimal("100"))
#                 gst_amount = total_item_price - (rate_excl_gst * quantity)
#             else:
#                 gst_amount = (gst / Decimal("100")) * total_item_price

#             total_item_price_final = (
#                 total_item_price if is_gst_inclusive else total_item_price + gst_amount
#             )

#             OrderItem.objects.create(
#                 order=order,
#                 product=product if product_id else None,
#                 product_variant=variant,
#                 quantity=quantity,
#                 price=price,
#                 total_price=total_item_price_final,
#                 gst=gst_amount,
#             )

#             processed_items.append({
#                 "product_name": product.name,
#                 "variant_name": variant.name if variant else None,
#                 "quantity": quantity,
#                 "price": round(price, 2),
#                 "gst": round(gst_amount, 2),
#             })

#             total_price += total_item_price_final
#             total_gst += gst_amount

#         order.total_price = total_price
#         order.gst = total_gst
#         order.save()

#         cgst = total_gst / 2
#         sgst = total_gst / 2
#         subtotal = total_price - total_gst

#         response_data = OrderSerializer(order).data
#         response_data.update({
#             "subtotal": round(subtotal, 2),
#             "cgst": round(cgst, 2),
#             "sgst": round(sgst, 2),
#             "customer": {
#                 "name": customer.name,
#                 "phone_number": customer.phone_number,
#             },
#             "items": processed_items,
#             "formatted_date": order.order_date.strftime("%d-%m-%Y %I:%M %p"),
#         })

#         return render(request, "bill.html", response_data)

#     except Exception as e:
#         return JsonResponse(
#             {"error": True, "details": str(e)},
#             status=500
#         )











@api_view(['POST'])
@permission_classes([AllowAny])
def print_kot(request, order_number):
    
    # Fetch order using order number
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product', 'items__product_variant'),
        order_number=order_number
    )

    items = order.items.all()

    context = {
        "order_number": order.order_number,
        "order_date": date_format(
            order.order_date,
            "Y-m-d H:i"
        ),
        "table_number": (
            order.table_number.table_number
            if order.table_number else None
        ),
        "note": order.note,

        "items": [
            {
                "product_name": (
                    item.product.name
                    if item.product else None
                ),
                "variant_name": (
                    item.product_variant.name
                    if item.product_variant else None
                ),
                "quantity": item.quantity,
                "status": item.status
            }
            for item in items
        ],
    }

    return render(
        request,
        "kot.html",
        context
    )














@api_view(['GET'])
@permission_classes([AllowAny])
def orders_past_three_hours(request, outlet_id):
    try:
        # Fetch all orders for outlet
        orders = Order.objects.filter(
            outlet_id=outlet_id
        ).order_by('-order_date')

        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 10
        result_page = paginator.paginate_queryset(orders, request)

        total_orders = orders.count()
        total_pages = paginator.page.paginator.num_pages
        current_page = paginator.page.number
        orders_on_current_page = len(result_page)

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
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "order_date": order.order_date,
                    "total_price": str(order.total_price),
                    "gst": str(order.gst),
                    "status": order.status,
                    "payment_status": order.payment_status,
                    "mode": order.mode,
                    "table_number": (
                        order.table_number.table_number
                        if order.table_number else None
                    )
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










# {
#   "product_ids": [1, 2],
#   "product_variant_ids": [10, 11]
# }



@swagger_auto_schema(
    method='post',
    operation_description="Mark products and/or product variants as stock out for a specific outlet.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'product_ids': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_INTEGER),
                description="List of product IDs to mark as stock out."
            ),
            'product_variant_ids': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_INTEGER),
                description="List of product variant IDs to mark as stock out."
            ),
        },
        required=[],
        example={
            "product_ids": [1, 2],
            "product_variant_ids": [10, 11]
        }
    ),
    responses={
        200: openapi.Response(
            description="Stock out status updated successfully.",
            examples={
                "application/json": {
                    "error": False,
                    "details": "Stock out status updated successfully."
                }
            }
        ),
        400: openapi.Response(
            description="Bad Request",
            examples={
                "application/json": {
                    "error": True,
                    "details": "Please provide either product_ids or product_variant_ids."
                }
            }
        ),
        500: openapi.Response(
            description="Internal Server Error",
            examples={
                "application/json": {
                    "error": True,
                    "details": "An error occurred: ..."
                }
            }
        ),
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def mark_items_stock_out(request, outlet_id):
    try:
        product_ids = request.data.get("product_ids", [])
        variant_ids = request.data.get("product_variant_ids", [])

        if not product_ids and not variant_ids:
            return Response({
                "error": True,
                "details": "Please provide either product_ids or product_variant_ids."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Mark products and their variants as stock out
        if product_ids:
            products = Product.objects.filter(id__in=product_ids, outlet_id=outlet_id)
            product_variants = ProductVariant.objects.filter(product__in=products)

            products.update(is_stock_out=True)
            product_variants.update(is_stock_out=True)

        # Mark variants as stock out only if their parent product is not already included
        if variant_ids:
            variants = ProductVariant.objects.filter(
                id__in=variant_ids,
                product__outlet_id=outlet_id
            ).exclude(product_id__in=product_ids)
            variants.update(is_stock_out=True)

        return Response({
            "error": False,
            "details": "Items Marked as Stocked Out successfully."
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "error": True,
            "details": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







# @api_view(['POST']) 
# @permission_classes([AllowAny])
# def send_order_notification(request):
#     registration_token = "fQVyajuyEYi_ZHPHEdR3se:APA91bEeDQbun4AVsH2Dm1axS2LwGpt2WFLql6NjBzrfCY8KnYRdmmJDQzHU3LpBiG_rsUX9fgV2OoxFBcmC9RHyAIiedz2GAvAKxGdDiiQWOpNUr2_8ggA"
    
#     try:
#         message = messaging.Message(
#             notification=messaging.Notification(
#                 title="Order Recieved",
#                 body="New Order Alert",
#             ),
#             token=registration_token,
#         )

#         response = messaging.send(message)
#         return Response(
#             {
#                 "error": False,
#                 "detail": "Message sent successfully",
#                 "response": response
#             },
#             status=status.HTTP_200_OK,
#         )

#     except Exception as e:
#         return Response(
#             {
#                 "error": True,
#                 "detail": str(e)
#             },
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         )



@api_view(["POST"])
@permission_classes([AllowAny])
def upload_billed_transaction(request, user_id, order_number):
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return Response(
            {"error": True, "detail": "User not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    amount = request.data.get("amount")
    if not amount:
        return Response(
            {"error": True, "detail": "Amount is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ✅ Generate order number HERE
    order_number = generate_order_number()
    
    # Prepare payload
    payload = {
        "TransactionNumber": order_number,
        "SequenceNumber": 1,
        "AllowedPaymentMode": "1",
        "Amount": amount,
        "UserID": user.username,   # ✅ take from CustomUser.username
        "MerchantID": 29610,
        "ClientID": 1013457,
        "StoreID": 1221258,
        "SecurityToken": "a4c9741b-2889-47b8-be2f-ba42081a246e",  # move to settings for security
        "AutoCancelDurationInMinutes": 5,
    }

    try:
        url = "https://www.plutuscloudserviceuat.in:8201/API/CloudBasedIntegration/V1/UploadBilledTransaction"
        response = requests.post(url, json=payload, timeout=30)
        response_data = response.json()
    except Exception as e:
        return Response(
            {"error": True, "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(
        {
            "error": False,
            "detail": "Transaction initiated",
            "order_number": order_number,  # ✅ send back
            "gateway_response": response_data,
        },
        status=response.status_code
    )










@swagger_auto_schema(
    method="post",
    operation_description="Check the status of a Plutus transaction using the PlutusTransactionReferenceID.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["transaction_id"],
        properties={
            "transaction_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="Plutus Transaction Reference ID"),
        },
    ),
    responses={
        200: openapi.Response("Transaction status retrieved successfully."),
        400: "Bad request (missing transaction_id).",
        404: "User not found.",
        500: "Plutus API error.",
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def get_transaction_status(request, user_id):
    # 🔹 Fetch user
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return Response({"error": True, "detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    # 🔹 Transaction ID required
    transaction_id = request.data.get("transaction_id")
    if not transaction_id:
        return Response({"error": True, "detail": "transaction_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    # 🔹 Payload for Plutus API
    payload = {
        "UserID": user.username,   # ✅ from CustomUser.username
        "MerchantID": 29610,
        "ClientID": 1013457,
        "StoreID": 1221258,
        "SecurityToken": "a4c9741b-2889-47b8-be2f-ba42081a246e",  # move to settings
        "PlutusTransactionReferenceID": transaction_id,
    }

    try:
        url = "https://www.plutuscloudserviceuat.in:8201/API/CloudBasedIntegration/V1/GetCloudBasedTxnStatus"
        response = requests.post(url, json=payload, timeout=30)
        response_data = response.json()
    except Exception as e:
        return Response({"error": True, "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"error": False, "status": response_data}, status=response.status_code)










@swagger_auto_schema(
    method="post",
    operation_description="Cancel a billed transaction in Plutus API.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["transaction_id", "amount"],
        properties={
            "transaction_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="PlutusTransactionReferenceID of the transaction to cancel."),
            "amount": openapi.Schema(type=openapi.TYPE_NUMBER, format="float", description="Amount of the transaction being cancelled."),
        },
    ),
    responses={
        200: openapi.Response("Transaction cancelled successfully."),
        400: "Bad request (missing required fields).",
        404: "User not found.",
        500: "Plutus API error.",
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def cancel_transaction(request, user_id):
    # 🔹 Fetch user
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return Response({"error": True, "detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    # 🔹 Validate request body
    transaction_id = request.data.get("transaction_id")
    amount = request.data.get("amount")

    if not transaction_id or not amount:
        return Response(
            {"error": True, "detail": "transaction_id and amount are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 🔹 Payload for Plutus API
    payload = {
        "UserID": user.username,  # ✅ from CustomUser.username (helps in tracking)
        "MerchantID": 29610,
        "ClientID": 1013457,
        "StoreID": 1221258,
        "SecurityToken": "a4c9741b-2889-47b8-be2f-ba42081a246e",  # ideally from settings
        "PlutusTransactionReferenceID": transaction_id,
        "Amount": amount
    }

    try:
        url = "https://www.plutuscloudserviceuat.in:8201/API/CloudBasedIntegration/V1/CancelTransaction"
        response = requests.post(url, json=payload, timeout=30)
        response_data = response.json()
    except Exception as e:
        return Response({"error": True, "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"error": False, "status": response_data}, status=response.status_code)







@swagger_auto_schema(
    method='get',
    operation_description="Get all tables of an outlet",
    manual_parameters=[
        openapi.Parameter(
            'outlet_id',
            openapi.IN_PATH,
            description="Outlet ID",
            type=openapi.TYPE_INTEGER
        )
    ],
    responses={200: TableSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_tables_by_outlet(request, outlet_id):
    outlet = get_object_or_404(Outlet, id=outlet_id)

    tables = Table.objects.filter(outlet=outlet).select_related('current_order')

    serializer = TableSerializer(tables, many=True)

    return Response({
        "error": False,
        "data": serializer.data
    }, status=status.HTTP_200_OK)






@swagger_auto_schema(
    method='patch',
    operation_description="Update table status",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['status'],
        properties={
            'status': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['empty', 'running', 'printing', 'paid', 'running_kot'],
                description="New table status"
            )
        }
    ),
    responses={
        200: openapi.Response(
            description="Table status updated successfully",
            examples={
                "application/json": {
                    "error": False,
                    "message": "Table status updated",
                    "data": {
                        "table_id": 1,
                        "table_number": 5,
                        "status": "running"
                    }
                }
            }
        ),
        400: openapi.Response(description="Invalid status"),
        404: openapi.Response(description="Table not found"),
    }
)
@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_table_status(request, table_id):
    try:
        table = get_object_or_404(Table, id=table_id)

        new_status = request.data.get("status")

        valid_status = ['empty', 'running', 'printing', 'paid', 'running_kot']

        if new_status not in valid_status:
            return Response({
                "error": True,
                "message": "Invalid status"
            }, status=status.HTTP_400_BAD_REQUEST)

        table.status = new_status

        # 🔥 Optional smart handling
        if new_status == "empty":
            table.current_order = None

        table.save()

        return Response({
            "error": False,
            "message": "Table status updated",
            "data": {
                "table_id": table.id,
                "table_number": table.table_number,
                "status": table.status
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "error": True,
            "details": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)








@swagger_auto_schema(
    method='post',
    operation_description="Add a new expense",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['title', 'amount'],
        properties={
            'title': openapi.Schema(type=openapi.TYPE_STRING),
            'description': openapi.Schema(type=openapi.TYPE_STRING),
            'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
        }
    ),
    responses={
        201: openapi.Response(
            description="Expense created successfully",
            schema=ExpenseSerializer
        ),
        400: openapi.Response(description="Invalid data")
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_expense(request, outlet_id):
    try:
        outlet = get_object_or_404(Outlet, id=outlet_id)

        serializer = ExpenseSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(outlet=outlet)

            return Response({
                "error": False,
                "message": "Expense added successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "error": True,
            "details": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            "error": True,
            "details": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)








@swagger_auto_schema(
    method='get',
    operation_description="Get all expenses of an outlet",
    responses={
        200: openapi.Response(
            description="List of expenses",
            schema=ExpenseSerializer(many=True)
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_expenses(request, outlet_id):
    try:
        outlet = get_object_or_404(Outlet, id=outlet_id)

        expenses = Expense.objects.filter(outlet=outlet).order_by('-expense_date')

        serializer = ExpenseSerializer(expenses, many=True)

        return Response({
            "error": False,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "error": True,
            "details": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@swagger_auto_schema(
    method='post',
    operation_description="Add items to existing order and generate KOT",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['items'],
        properties={
            'items': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'product': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'product_variant': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'quantity': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            )
        }
    ),
    responses={200: openapi.Response(description="Items added + KOT created")}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_items_to_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id)

        # 🔥 If already completed → reopen
        if order.status == "settled":
            order.status = "processing"
            order.save()

        items_data = request.data.get("items")
        table = order.table_number

        kot_items = []
        total_price = order.total_price
        total_gst = order.gst

        for item in items_data:
            product = None
            variant = None

            if item.get("product"):
                product = Product.objects.get(id=item["product"])
                price = product.price
                gst = product.gst_percentage or 0
            else:
                variant = ProductVariant.objects.get(id=item["product_variant"])
                product = variant.product
                price = variant.price
                gst = product.gst_percentage or 0

            quantity = item["quantity"]

            total_item_price = price * quantity
            gst_amount = (gst / 100) * total_item_price

            OrderItem.objects.create(
                order=order,
                product=product if item.get("product") else None,
                product_variant=variant,
                quantity=quantity,
                price=price,
                total_price=total_item_price + gst_amount,
                gst=gst_amount,
                status="processing"
            )

            kot_items.append({
                "product_id": product.id,
                "product_name": product.name,
                "quantity": quantity
            })

            total_price += total_item_price + gst_amount
            total_gst += gst_amount

        order.total_price = total_price
        order.gst = total_gst
        order.save()

        # 🔥 Create KOT
        kot_count = KOT.objects.filter(order=order).count() + 1

        kot = KOT.objects.create(
            table=table,
            order=order,
            kot_number=kot_count,
            items=kot_items
        )

        # Update table status
        table.status = "running_kot"
        table.save()

        return Response({
            "error": False,
            "message": "Items added and KOT created",
            "kot_number": kot.kot_number
        })

    except Exception as e:
        return Response({"error": True, "details": str(e)})
    
    
    
    




@swagger_auto_schema(
    method='get',
    operation_description="Get table details with all KOTs",
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_table_with_kot(request, table_id):
    try:
        table = Table.objects.get(id=table_id)

        # 🚫 Hide KOTs for specific statuses
        if table.status in ['empty', 'pending_counter_confirmation']:
            return Response({
                "table_number": table.table_number,
                "status": table.status,
                "kots": []  # no KOTs shown
            })

        kots = table.kots.all().order_by('kot_number')

        kot_data = [
            {
                "kot_number": kot.kot_number,
                "items": kot.items,
                "created_at": kot.created_at
            }
            for kot in kots
        ]

        return Response({
            "table_number": table.table_number,
            "status": table.status,
            "kots": kot_data
        })

    except Table.DoesNotExist:
        return Response({"error": True, "details": "Table not found"}, status=404)
    except Exception as e:
        return Response({"error": True, "details": str(e)}, status=500)
    
    






@swagger_auto_schema(
    method='patch',
    operation_description="Update single order item status",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['status'],
        properties={
            'status': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['processing', 'rejected', 'ready_to_serve']
            )
        }
    ),
    responses={200: openapi.Response(description="Item status updated")}
)
@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_order_item_status(request, item_id):
    try:
        item = get_object_or_404(OrderItem, id=item_id)
        new_status = request.data.get("status")

        valid_status = ['processing', 'rejected', 'ready_to_serve']

        if new_status not in valid_status:
            return Response({"error": True, "message": "Invalid status"}, status=400)

        item.status = new_status
        item.save()

        # 🔥 Sync order status
        order = item.order
        items = order.items.all()

        if all(i.status == 'ready_to_serve' for i in items):
            order.status = "confirmed"
        elif any(i.status == 'processing' for i in items):
            order.status = "processing"

        order.save()

        return Response({
            "error": False,
            "message": "Item status updated",
            "data": {
                "item_id": item.id,
                "status": item.status
            }
        })

    except Exception as e:
        return Response({"error": True, "details": str(e)}, status=500)






@swagger_auto_schema(
    method='patch',
    operation_description="Bulk update order items status",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['items'],
        properties={
            'items': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'item_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'status': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            enum=['processing', 'rejected', 'ready_to_serve']
                        )
                    }
                )
            )
        }
    ),
    responses={200: openapi.Response(description="Bulk update success")}
)
@api_view(['PATCH'])
@permission_classes([AllowAny])
def bulk_update_order_items(request):
    try:
        items_data = request.data.get("items", [])

        updated_items = []
        order_ids = set()

        for item in items_data:
            order_item = OrderItem.objects.get(id=item['item_id'])
            order_item.status = item['status']
            order_item.save()

            updated_items.append(order_item.id)
            order_ids.add(order_item.order.id)

        # 🔥 Sync each order
        for order_id in order_ids:
            order = Order.objects.get(id=order_id)
            items = order.items.all()

            if all(i.status == 'ready_to_serve' for i in items):
                order.status = "confirmed"
            elif any(i.status == 'processing' for i in items):
                order.status = "processing"

            order.save()

        return Response({
            "error": False,
            "message": "Bulk update successful",
            "updated_items": updated_items
        })

    except Exception as e:
        return Response({"error": True, "details": str(e)}, status=500)





@swagger_auto_schema(
    method='post',
    operation_description="Settle order with single or multiple payments",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['payments'],
        properties={
            'payments': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(
                    type=openapi.TYPE_OBJECT,
                    required=['amount', 'payment_mode'],
                    properties={
                        'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'payment_mode': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            enum=['upi', 'cash', 'card', 'coupon']
                        ),
                        'transaction_id': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        }
    ),
    responses={200: openapi.Response(description="Order settled")}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def settle_order(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id)
        
        if order.status not in ["completed", "payment_pending"]:
            return Response({
                "error": True,
                "message": "Order not ready for settlement"
            }, status=400)

        payments_data = request.data.get("payments", [])

        if not payments_data:
            return Response({
                "error": True,
                "message": "At least one payment is required"
            }, status=400)

        total_paid = 0

        # 🔥 Create payment entries
        for payment in payments_data:
            amount = float(payment.get("amount", 0))
            mode = payment.get("payment_mode")

            if not amount or not mode:
                return Response({
                    "error": True,
                    "message": "Invalid payment data"
                }, status=400)

            OrderPayment.objects.create(
                order=order,
                amount=amount,
                payment_mode=mode,
                transaction_id=payment.get("transaction_id")
            )

            total_paid += amount

        # 🔥 Validate total payment
        if total_paid < float(order.total_price):
            return Response({
                "error": True,
                "message": f"Insufficient payment. Paid {total_paid}, required {order.total_price}"
            }, status=400)

        # ✅ Update order
        order.status = "settled"
        order.payment_status = "success"
        order.mode = payments_data[0]["payment_mode"]
        order.save()

        # 🔥 Table handling
        table = order.table_number
        if table:
            table.status = "paid"
            table.current_order = None
            table.save()

        return Response({
            "error": False,
            "message": "Order settled successfully",
            "data": {
                "order_id": order.id,
                "order_number": order.order_number,
                "total_bill": float(order.total_price),
                "total_paid": total_paid,
                "status": order.status,
                "payments": payments_data
            }
        })

    except Exception as e:
        return Response({"error": True, "details": str(e)}, status=500)





check_status_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['ptrn'],
    properties={
        'ptrn': openapi.Schema(type=openapi.TYPE_STRING)
    }
)

@swagger_auto_schema(
    method='post',
    operation_description="Check PineLabs transaction status",
    request_body=check_status_schema
)
@api_view(['POST'])
@permission_classes([AllowAny])
def check_payment_status(request):
    try:
        ptrn = request.data.get("ptrn")

        payload = {
            "MerchantID": settings.PINELABS_MERCHANT_ID,
            "SecurityToken": settings.PINELABS_SECURITY_TOKEN,
            "ClientId": settings.PINELABS_CLIENT_ID,
            "StoreId": settings.PINELABS_STORE_ID,
            "PlutusTransactionReferenceID": ptrn,
        }

        res = requests.post(
            f"{settings.PINELABS_BASE_URL}/GetTransactionStatus",
            json=payload
        )

        return JsonResponse(res.json())

    except Exception as e:
        return JsonResponse({"error": True, "details": str(e)}, status=500)





confirm_payment_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['order_number', 'status'],
    properties={
        'order_number': openapi.Schema(type=openapi.TYPE_STRING),
        'status': openapi.Schema(type=openapi.TYPE_STRING, description="SUCCESS / FAILED"),
    }
)

@swagger_auto_schema(
    method='post',
    operation_description="Confirm payment after frontend polling",
    request_body=confirm_payment_schema
)
@api_view(['POST'])
@permission_classes([AllowAny])
def confirm_payment(request):
    try:
        order_number = request.data.get("order_number")
        status = request.data.get("status")

        order = Order.objects.get(order_number=order_number)

        if status == "SUCCESS":
            order.status = "confirmed"
            order.payment_status = "success"
        else:
            order.status = "cancelled"
            order.payment_status = "failed"

        order.save()

        return JsonResponse({
            "error": False,
            "message": "Order updated",
            "order_status": order.status
        })

    except Order.DoesNotExist:
        return JsonResponse({"error": True, "message": "Order not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": True, "details": str(e)}, status=500)
    
    
    

STATUS_TRANSITIONS = {
    'draft': ['pending', 'cancelled'],
    'pending': ['processing', 'rejected'],
    'processing': ['ready', 'rejected'],
    'ready': ['completed'],
    'completed': ['payment_pending'],
    'payment_pending': ['settled'],
    'settled': [],
    'cancelled': [],
    'rejected': [],
}


@swagger_auto_schema(
    method='patch',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['status'],
        properties={
            'status': openapi.Schema(type=openapi.TYPE_STRING)
        }
    )
)
@api_view(['PATCH'])
@permission_classes([AllowAny])
def change_order_status(request, order_id):
    try:
        order = Order.objects.select_related('table_number').get(id=order_id)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)

    new_status = request.data.get('status')

    if not new_status:
        return Response({"error": "Status is required"}, status=400)

    # 🚫 Removed transition validation
    # 🚫 Removed STATUS_TRANSITIONS check

    # Optional: still prevent update after settlement (remove if not needed)
    if order.status == 'settled':
        return Response({
            "error": "Cannot change status after settlement"
        }, status=400)

    order.status = new_status
    order.save()

    # 🔥 OPTIONAL: Update table status
    if order.table_number:
        if new_status in ['pending', 'processing']:
            order.table_number.status = 'running_kot'
        elif new_status == 'completed':
            order.table_number.status = 'running'
        elif new_status == 'settled':
            order.table_number.status = 'paid'

        order.table_number.save()

    return Response({
        "message": "Order status updated successfully",
        "order_id": order.id,
        "new_status": order.status
    })







@swagger_auto_schema(method='delete')
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_draft_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)

    if order.status != 'draft':
        return Response({
            "error": "Only draft orders can be deleted"
        }, status=400)

    order.delete()

    return Response({
        "message": "Draft order deleted successfully"
    })


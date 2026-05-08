from django.shortcuts import render

import random
import string
import base64
import json
import qrcode
from io import BytesIO
import os

from decimal import Decimal

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework import status

from PIL import Image, ImageDraw, ImageFont

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from firebase_admin import messaging

from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.utils.timezone import localtime
from django.db.models import Q
from django.conf import settings
from django.template.loader import render_to_string

from v1.models import (
    Outlet,
    Category,
    Product,
    ProductVariant,
    Order,
    OrderItem,
    Customer,
    Coupon,
    RazorpayCredential,
    FCMToken, 
    Table
)

from .models import (
    QRCustomization,
    SpecialMenu,
    AdvertisementBanner,
    OutletTableConfiguration,
    TableQR
)

from .serializers import (
    ProductSerializer,
    ProductVariantSerializer,
    OrderItemSerializer,
    OrderSerializer,
    CouponSerializer,
    RazorpayCredentialSerializer,
    OutletSerializer,
    QRCustomizationSerializer,
    AdvertisementBannerSerializer,
    SpecialMenuSerializer,
    OutletTableConfigurationSerializer,
    TableQRSerializer
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
def category_list(request, outlet_id):
    try:
        # Check if the outlet exists
        outlet = Outlet.objects.get(id=outlet_id)

        # Get the categories for the given outlet with both id and name
        categories = Category.objects.filter(outlet=outlet).values('id', 'name')

        return Response({
            "error": False,
            "detail": "Categories fetched successfully.",
            "sequence":1,
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
def product_list(request, outlet_id):
    try:
        # Fetch the outlet to ensure it exists
        outlet = get_object_or_404(Outlet, id=outlet_id)

        # Get query parameters
        is_veg = request.query_params.get('isVeg', 'true').lower() == 'true'
        is_nonveg = request.query_params.get('isNonveg', 'true').lower() == 'true'

        # Apply filtering logic based on the query parameters
        if is_veg and not is_nonveg:
            products = Product.objects.filter(outlet=outlet, is_veg=True)
        elif not is_veg and is_nonveg:
            products = Product.objects.filter(outlet=outlet, is_veg=False)
        else:
            products = Product.objects.filter(outlet=outlet)  # No filtering on is_veg

        products = products.select_related('category').prefetch_related('variants').all()

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
            product_data = ProductSerializer(product, context={'request': request}).data
            category_dict[category_id]["items"].append(product_data)

        # Convert the dictionary to a list
        response_data = list(category_dict.values())

        return Response({
            "error": False,
            "details": "Products fetched successfully",
            "sequence": 3,
            "categories": response_data
        })
    except Exception as e:
        return Response({
            "error": True,
            "details": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    


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






def generate_order_number(length=12):
    """Generate a random order number with uppercase letters and digits."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# {
#     "customer": {
#         "name": "John Doe",
#         "phone_number": "999999999"
#     },
#     "items": [
#         {
#             "product": 2,
#             "quantity": 2
#         }
#     ],
#     "mode": "UPI"

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
    try:
        data = request.data
        customer_data = data.get('customer')
        items_data = data.get('items')
        mode = data.get('mode', '')  # Extract mode early
        coupon = data.get('coupon', '')  # Extract mode early
        table_number = data.get('table_number')
        
        # Razorpay fields
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')

        # Check for Customer
        customer = Customer.objects.filter(
            name=customer_data.get('name'),
            phone_number=customer_data.get('phone_number')
        ).first()
        
        if not customer:
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
            # address=data.get('address', ''),
            mode=mode,
            table_number=table_number,  # ✅ Save table number here
            razorpay_order_id=razorpay_order_id if mode == 'upi' else None,
            razorpay_payment_id=razorpay_payment_id if mode == 'upi' else None,
            razorpay_signature=razorpay_signature if mode == 'upi' else None,
        )

        customer.order = order
        customer.save()

        total_price = Decimal('0.00')
        total_gst = Decimal('0.00')
        processed_items = []

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
                rate_excluding_gst = price / (1 + gst / Decimal('100'))
                gst_amount = total_item_price - (rate_excluding_gst * quantity)
                amount_excluding_gst = total_item_price - gst_amount
            else:
                gst_amount = (gst / Decimal('100')) * total_item_price
                rate_excluding_gst = price
                amount_excluding_gst = total_item_price

            total_item_gst_inclusive = total_item_price + gst_amount if not is_gst_inclusive else total_item_price

            OrderItem.objects.create(
                order=order,
                product=product if product_id else None,
                product_variant=variant if variant_id else None,
                quantity=quantity,
                price=price,
                total_price=total_item_gst_inclusive,
                gst=gst_amount
            )

            processed_items.append({
                "product_name": product.name,
                "variant_name": variant.name if variant_id else None,
                "quantity": quantity,
                "price": round(rate_excluding_gst, 2),
                "total_price": round(amount_excluding_gst, 2),
                "gst": round(gst_amount, 2),
            })

            total_price += total_item_gst_inclusive
            total_gst += gst_amount

        subtotal = total_price - total_gst
        order.total_price = total_price
        order.gst = total_gst
        order.save()

        cgst = total_gst / 2
        sgst = total_gst / 2

        order_serializer = OrderSerializer(order, context={'request': request})
        response_data = order_serializer.data

        response_data['subtotal'] = round(subtotal, 2)
        response_data['formatted_date'] = order.order_date.strftime("%d-%m-%Y %I:%M %p")
        response_data['customer'] = {
            "name": customer.name,
            "phone_number": customer.phone_number
        }
        response_data['items'] = processed_items
        response_data['cgst'] = round(cgst, 2)
        response_data['sgst'] = round(sgst, 2)
        
        
        #FCM message integration
        fcm_token_obj = FCMToken.objects.filter(outlet_id=outlet_id).first()
        if fcm_token_obj:
            notification_result = send_order_notification(fcm_token_obj.token)
            print("Notification response:", notification_result)
        else:
            print("No FCM token found for this outlet.")
        
        

        return Response(response_data, status=status.HTTP_201_CREATED)

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

        
        
    
    
    
    # # Fetch the outlet from the URL parameter
    # outlet = get_object_or_404(Outlet, id=outlet_id)

    # # Add the outlet to the request data for the serializer
    # request.data['outlet'] = outlet.id

    # # Initialize the serializer with the data and validate
    # serializer = OrderSerializer(data=request.data)

    # if serializer.is_valid():
    #     order_data = serializer.validated_data
    #     order_data['order_number'] = generate_order_number()

    #     # Remove items from order_data, as they should be handled separately
    #     items_data = request.data.get('items', [])
        
    #     # Handle the creation of the order
    #     order = Order.objects.create(
    #         order_number=order_data['order_number'],
    #         order_date=order_data['order_date'],
    #         mode=order_data['mode'],
    #         total_price=order_data['total_price'],
    #         gst=order_data['gst'],
    #         outlet=outlet  # Associate the outlet with the order
    #     )

    #     # Extract customer data and create a Customer associated with the created order
    #     customer_data = request.data.get('customer', {})
    #     customer = Customer.objects.create(
    #         name=customer_data.get('name'),
    #         phone_number=customer_data.get('phone'),
    #         order=order  # Associate the customer with the created order
    #     )

    #     # Process the order items
    #     items_list = []  # To store item details for the response
    #     for item_data in items_data:
    #         product = None
    #         product_variant = None
    #         price = 0.0
    #         gst_percent = 0.0
    #         total_price = 0.0
    #         gst_amount = 0.0
    #         product_name = None
    #         product_variant_name = None

    #         # Fetch product or product variant
    #         if 'product' in item_data:
    #             product = get_object_or_404(Product, id=item_data['product'])
    #             price = product.price
    #             gst_percent = product.gst_percentage
    #             product_name = product.name  # Get the product name
                
    #             # If GST is not inclusive, calculate the price including GST
    #             if not product.is_gst_inclusive:
    #                 gst_amount = (gst_percent / 100) * price
    #                 total_price = price + gst_amount  # Add GST to price
    #             else:
    #                 total_price = price  # Price already includes GST

    #         elif 'product_variant' in item_data:
    #             product_variant = get_object_or_404(ProductVariant, id=item_data['product_variant'])
    #             product = product_variant.product
    #             price = product_variant.price
    #             gst_percent = product.gst_percentage
    #             product_variant_name = product_variant.name  # Get the product variant name
                
    #             # If GST is not inclusive, calculate the price including GST
    #             if not product_variant.is_gst_inclusive:
    #                 gst_amount = (gst_percent / 100) * price
    #                 total_price = price + gst_amount  # Add GST to price
    #             else:
    #                 total_price = price  # Price already includes GST

    #         # Calculate total price for the quantity and GST for the item
    #         quantity = item_data['quantity']
    #         total_price = total_price * quantity
    #         gst_amount = (gst_percent / 100) * total_price if not product.is_gst_inclusive else 0

    #         # Create the order item associated with the order
    #         order_item = OrderItem.objects.create(
    #             order=order,
    #             product=product,
    #             product_variant=product_variant,
    #             quantity=quantity,
    #             price=price,
    #             total_price=total_price,
    #             gst=gst_amount
    #         )

    #         # Append item details for the response
    #         items_list.append({
    #             'product_name': product_name,
    #             'product_variant_name': product_variant_name,
    #             'quantity': item_data['quantity'],
    #             'price': price,
    #             'total_price': total_price,
    #             'gst': gst_amount,
    #         })

    #     # Serialize the entire order including customer and items
    #     order_details = {
    #         'error': False,
    #         'detail': 'Order placed successfully',
    #         'order_number': order.order_number,
    #         'customer': {
    #             'name': customer.name,
    #             'phone_number': customer.phone_number
    #         },
    #         'items': items_list
    #     }

    #     return Response(order_details, status=status.HTTP_201_CREATED)

    # # Return detailed validation errors if the serializer is invalid
    # return Response({
    #     'error': True,
    #     'detail': 'Validation failed',
    #     'errors': serializer.errors
    # }, status=status.HTTP_400_BAD_REQUEST)
    
    
    
    
    
    

special_menu_get_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "error": openapi.Schema(type=openapi.TYPE_BOOLEAN),
        "details": openapi.Schema(type=openapi.TYPE_STRING),
        "menu_name": openapi.Schema(type=openapi.TYPE_STRING),
        "products": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                # You can define nested product structure or just refer to ProductSerializer output
                # For simplicity, just type object here
                description="Product with variants"
            ),
        ),
    },
)

@swagger_auto_schema(
    method="get",
    operation_description="Retrieve all special menus for a given outlet (with their products).",
    responses={
        200: SpecialMenuSerializer(many=True),
        404: "Outlet not found or no special menus available.",
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def get_special_menu(request, outlet_id):
    try:
        menus = SpecialMenu.objects.filter(outlet_id=outlet_id)
        if not menus.exists():
            return Response(
                {"error": True, "detail": "No special menus found for this outlet."},
                status=status.HTTP_404_NOT_FOUND,
            )
    except Exception:
        return Response({"error": True, "detail": "Outlet not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = SpecialMenuSerializer(menus, many=True)
    return Response(
        {"error": False, "special_menus": serializer.data},
        status=status.HTTP_200_OK,
    )

        
        
        
        





@swagger_auto_schema(
    method="post",
    operation_description="Create a new advertisement banner for an outlet.",
    request_body=AdvertisementBannerSerializer,
    responses={
        201: "Banner created successfully.",
        400: "Bad request.",
        404: "Outlet not found."
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def create_banner(request, outlet_id):
    try:
        outlet = Outlet.objects.get(id=outlet_id)
    except Outlet.DoesNotExist:
        return Response({"error": True, "detail": "Outlet not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = AdvertisementBannerSerializer(data=request.data)
    if serializer.is_valid():
        banner = serializer.save(outlet=outlet)
        return Response({"error": False, "detail": "Banner created successfully.", "data": AdvertisementBannerSerializer(banner).data}, status=status.HTTP_201_CREATED)
    return Response({"error": True, "detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# LIST banners for an outlet
@swagger_auto_schema(
    method="get",
    operation_description="Get all advertisement banners for an outlet.",
    responses={200: AdvertisementBannerSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def list_banners(request, outlet_id):
    banners = AdvertisementBanner.objects.filter(outlet_id=outlet_id)
    serializer = AdvertisementBannerSerializer(banners, many=True)
    return Response({"error": False, "banners": serializer.data}, status=status.HTTP_200_OK)


# RETRIEVE a single banner
@swagger_auto_schema(
    method="get",
    operation_description="Retrieve a single advertisement banner by ID.",
    responses={200: AdvertisementBannerSerializer, 404: "Banner not found."},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def get_banner(request, banner_id):
    try:
        banner = AdvertisementBanner.objects.get(id=banner_id)
    except AdvertisementBanner.DoesNotExist:
        return Response({"error": True, "detail": "Banner not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = AdvertisementBannerSerializer(banner)
    return Response({"error": False, "banner": serializer.data}, status=status.HTTP_200_OK)


# UPDATE
@swagger_auto_schema(
    method="put",
    operation_description="Update an advertisement banner.",
    request_body=AdvertisementBannerSerializer,
    responses={200: "Banner updated successfully.", 400: "Bad request.", 404: "Banner not found."},
)
@api_view(["PUT"])
@permission_classes([AllowAny])
def update_banner(request, banner_id):
    try:
        banner = AdvertisementBanner.objects.get(id=banner_id)
    except AdvertisementBanner.DoesNotExist:
        return Response({"error": True, "detail": "Banner not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = AdvertisementBannerSerializer(banner, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"error": False, "detail": "Banner updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)
    return Response({"error": True, "detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# DELETE
@swagger_auto_schema(
    method="delete",
    operation_description="Delete an advertisement banner.",
    responses={204: "Banner deleted successfully.", 404: "Banner not found."},
)
@api_view(["DELETE"])
@permission_classes([AllowAny])
def delete_banner(request, banner_id):
    try:
        banner = AdvertisementBanner.objects.get(id=banner_id)
    except AdvertisementBanner.DoesNotExist:
        return Response({"error": True, "detail": "Banner not found."}, status=status.HTTP_404_NOT_FOUND)

    banner.delete()
    return Response({"error": False, "detail": "Banner deleted successfully."}, status=status.HTTP_204_NO_CONTENT)









@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all active coupons with their details like min cart value, expiry, applicable products/categories, and discount rules.",
    responses={
        200: openapi.Response(
            description="Successful Response",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'details': openapi.Schema(type=openapi.TYPE_STRING),
                    'coupons': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Items(type=openapi.TYPE_OBJECT)
                    ),
                },
            )
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def active_coupons(request,outlet_id):
    try:
        # Check if the outlet exists
        outlet = Outlet.objects.filter(id=outlet_id).first()
        now = timezone.now()
        coupons = Coupon.objects.filter(outlet=outlet).filter(is_active=True).filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gt=now)
        )
        serializer = CouponSerializer(coupons, many=True)
        return Response({
            "error": False,
            "details": "Active coupons fetched successfully",
            "coupons": serializer.data
        })
    except Exception as e:
        return Response({
            "error": True,
            "details": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'outlet_id', openapi.IN_PATH,
            description="ID of the outlet",
            type=openapi.TYPE_INTEGER
        )
    ],
    responses={
        200: openapi.Response(
            description="Base64 encoded JSON with Razorpay credentials",
            examples={
                "application/json": {
                    "data": "eyJlcnJvciI6ZmFsc2UsImRldGFpbHMiOnsicmF6b3JwYXlfY2xpZW50X2lkIjoiY2xpZW50X2lkXzEyMyIsInJhem9ycGF5X3NlY3JldCI6InNlY3JldF8xMjMifX0="
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_razorpay_credentials(request, outlet_id):
    try:
        credential = RazorpayCredential.objects.get(outlet_id=outlet_id)
        serializer = RazorpayCredentialSerializer(credential)
        
        response_data = {
            "error": False,
            "credentials": serializer.data
        }
    except RazorpayCredential.DoesNotExist:
        response_data = {
            "error": True,
            "details": "Credentials not found for this outlet."
        }

    # Base64 encode the full response
    json_data = json.dumps(response_data)
    base64_data = base64.b64encode(json_data.encode()).decode()

    return Response({base64_data})




#   name: "Mantra POS",
#   description: "Enjoy your meal!",
#   image: "/window.svg",
#   theme: {
#     color: "#F37254",
#     backdrop_color: "#fff",
#   },






@swagger_auto_schema(
    method='get',
    responses={200: OutletSerializer()}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_outlet_details(request, outlet_id):
    # Retrieve the outlet object or return 404 if not found
    outlet = get_object_or_404(Outlet, id=outlet_id)

    # Retrieve the associated company object
    company = outlet.company

    # Retrieve the QR customization for the outlet, if any
    qr_customization = QRCustomization.objects.filter(outlet=outlet).first()

    # Prepare the response data
    data = {
        "outlet_details": {
            "outlet_name": outlet.outlet_name,
            "address": outlet.address,
            "phone_number": outlet.phone_number,
            "gst_number": outlet.gst_number,
            "opening_hours": outlet.opening_hours,
            "is_active": outlet.is_active,
            "logo": request.build_absolute_uri(outlet.logo.url) if outlet.logo else None,
        },
        "company_details": {
            "company_name": company.name,
            "address": company.address,
        },
        "qr_customization_details": {
            "qr_tagline": qr_customization.qr_tagline if qr_customization else None,
            "qr_logo": request.build_absolute_uri(qr_customization.qr_logo.url) if qr_customization and qr_customization.qr_logo else None,
            "theme_color": qr_customization.theme_color if qr_customization else None,
        }
    }

    return Response(data, status=status.HTTP_200_OK)

# def get_outlet_details(request, outlet_id):
#     # Retrieve the outlet object or return 404 if not found
#     outlet = get_object_or_404(Outlet, id=outlet_id)

#     # Use the serializer to return the outlet, company, and QR customization data
#     serializer = OutletSerializer(outlet, context={'request': request})

#     return Response(serializer.data, status=status.HTTP_200_OK)





@swagger_auto_schema(
    method='post',
    request_body=RazorpayCredentialSerializer,
    responses={
        200: RazorpayCredentialSerializer,
        400: 'Bad Request',
        404: 'Outlet not found'
    },
    operation_summary="Add or update Razorpay credentials for an outlet"
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_or_update_razorpay_credentials(request, outlet_id):
    try:
        outlet = Outlet.objects.get(id=outlet_id)
    except Outlet.DoesNotExist:
        return Response({"detail": "Outlet not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        credential = RazorpayCredential.objects.get(outlet=outlet)
        serializer = RazorpayCredentialSerializer(credential, data=request.data)
    except RazorpayCredential.DoesNotExist:
        serializer = RazorpayCredentialSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(outlet=outlet)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)












@swagger_auto_schema(
    method='post',
    request_body=QRCustomizationSerializer,
    responses={
        200: QRCustomizationSerializer,
        400: 'Bad Request',
        404: 'Outlet not found'
    },
    operation_summary="Add or update QR customization settings for an outlet"
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_or_update_qr_customization(request, outlet_id):
    try:
        outlet = Outlet.objects.get(id=outlet_id)
    except Outlet.DoesNotExist:
        return Response({"detail": "Outlet not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        customization = QRCustomization.objects.get(outlet=outlet)
        serializer = QRCustomizationSerializer(customization, data=request.data, partial=True)
    except QRCustomization.DoesNotExist:
        serializer = QRCustomizationSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(outlet=outlet)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)










# {
#   "name": "Evening Snacks",
#   "products": [1, 2, 3]
# }

special_menu_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['name', 'products'],
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Special menu name'),
        'products': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Items(type=openapi.TYPE_INTEGER),
            description='List of product IDs (max 5)'
        ),
    },
)

special_menu_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "error": openapi.Schema(type=openapi.TYPE_BOOLEAN),
        "details": openapi.Schema(type=openapi.TYPE_STRING),
        "menu": openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                "name": openapi.Schema(type=openapi.TYPE_STRING),
                "products": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER)),
            },
        ),
    },
)

# ---------------- CREATE SPECIAL MENU ----------------
@swagger_auto_schema(
    method="post",
    operation_description="Create a new special menu. Products are optional (max 5 if provided).",
    request_body=SpecialMenuSerializer,
    responses={
        201: "Special menu created successfully.",
        400: "Bad request.",
        401: "Unauthorized.",
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def create_special_menu(request):
    serializer = SpecialMenuSerializer(data=request.data)
    if serializer.is_valid():
        special_menu = serializer.save()
        return Response(
            {"error": False, "detail": "Special menu created successfully.", "menu": serializer.data},
            status=status.HTTP_201_CREATED,
        )
    return Response({"error": True, "detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ---------------- ADD PRODUCT TO SPECIAL MENU ----------------
product_id_param = openapi.Parameter(
    "product_id", openapi.IN_PATH, description="ID of the product to add", type=openapi.TYPE_INTEGER
)

@swagger_auto_schema(
    method="post",
    manual_parameters=[product_id_param],
    operation_description="Add a single product to a special menu (max 5 products allowed).",
    responses={
        200: "Product added successfully.",
        400: "Bad request (e.g., product already exists, exceeds limit).",
        404: "Special menu or product not found.",
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def add_product_to_special_menu(request, menu_id, product_id):
    try:
        menu = SpecialMenu.objects.get(id=menu_id)
    except SpecialMenu.DoesNotExist:
        return Response({"error": True, "detail": "Special menu not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({"error": True, "detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

    if menu.products.count() >= 5:
        return Response({"error": True, "detail": "A Special Menu can contain a maximum of 5 products."},
                        status=status.HTTP_400_BAD_REQUEST)

    if product in menu.products.all():
        return Response({"error": True, "detail": "Product already exists in the special menu."},
                        status=status.HTTP_400_BAD_REQUEST)

    menu.products.add(product)
    return Response({"error": False, "detail": "Product added successfully."}, status=status.HTTP_200_OK)


# ---------------- REMOVE PRODUCT FROM SPECIAL MENU ----------------
@swagger_auto_schema(
    method="delete",
    manual_parameters=[product_id_param],
    operation_description="Remove a single product from a special menu.",
    responses={
        200: "Product removed successfully.",
        404: "Special menu or product not found.",
    },
)
@api_view(["DELETE"])
@permission_classes([AllowAny])
def remove_product_from_special_menu(request, menu_id, product_id):
    try:
        menu = SpecialMenu.objects.get(id=menu_id)
    except SpecialMenu.DoesNotExist:
        return Response({"error": True, "detail": "Special menu not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({"error": True, "detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

    if product not in menu.products.all():
        return Response({"error": True, "detail": "Product not found in this menu."}, status=status.HTTP_400_BAD_REQUEST)

    menu.products.remove(product)
    return Response({"error": False, "detail": "Product removed successfully."}, status=status.HTTP_200_OK)











update_name_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['name'],
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description='New name for the special menu'),
    },
)

update_name_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "error": openapi.Schema(type=openapi.TYPE_BOOLEAN),
        "details": openapi.Schema(type=openapi.TYPE_STRING),
        "menu_name": openapi.Schema(type=openapi.TYPE_STRING),
    },
)

@swagger_auto_schema(
    method='patch',
    request_body=update_name_request,
    responses={
        200: update_name_response,
        400: 'Bad Request',
        404: 'Outlet or special menu not found'
    },
    operation_summary="Update the name of the special menu for an outlet"
)
@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_special_menu_name(request, outlet_id):
    try:
        outlet = Outlet.objects.filter(id=outlet_id).first()
        if not outlet:
            return Response({
                "error": True,
                "details": "Outlet not found."
            }, status=status.HTTP_404_NOT_FOUND)

        special_menu = SpecialMenu.objects.filter(outlet=outlet).first()
        if not special_menu:
            return Response({
                "error": True,
                "details": "Special menu not found for this outlet."
            }, status=status.HTTP_404_NOT_FOUND)

        new_name = request.data.get("name")
        if not new_name:
            return Response({
                "error": True,
                "details": "Name is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        special_menu.name = new_name
        special_menu.save()

        return Response({
            "error": False,
            "details": "Special menu name updated successfully.",
            "menu_name": special_menu.name
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "error": True,
            "details": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@swagger_auto_schema(
    method='post',
    operation_summary="Generate QR codes for all tables in an outlet",
    operation_description="""
This endpoint generates QR codes for all tables of a given outlet.

### ✅ Behavior:
- If tables exist → QR codes are generated for each table
- If no tables exist → returns message: "No tables are present"

### 🔗 QR Format:
Each QR contains:
**table_id=<table_id>**

(Recommended: Replace with frontend URL like  
`https://yourdomain.com/menu?table_id=<table_id>`)

### 📌 Notes:
- QR codes are generated dynamically based on existing `Table` records
- No dependency on table configuration or TableQR model
""",
    responses={
        200: openapi.Response(
            description="QRs generated successfully",
            examples={
                "application/json": {
                    "error": False,
                    "outlet_id": 1,
                    "total_tables": 3,
                    "tables": [
                        {
                            "table_number": 1,
                            "table_id": "TBL001",
                            "location": "Ground Floor",
                            "qr_data": "table_id=TBL001",
                            "qr_image": "(generated) table_1.png"
                        },
                        {
                            "table_number": 2,
                            "table_id": "TBL002",
                            "location": "First Floor",
                            "qr_data": "table_id=TBL002",
                            "qr_image": "(generated) table_2.png"
                        }
                    ]
                }
            }
        ),

        200: openapi.Response(
            description="No tables present",
            examples={
                "application/json": {
                    "error": False,
                    "message": "No tables are present for this outlet"
                }
            }
        ),

        404: openapi.Response(
            description="Outlet not found",
            examples={
                "application/json": {
                    "error": True,
                    "message": "Outlet not found"
                }
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def generate_table_qrs(request, outlet_id):

    try:
        outlet = Outlet.objects.get(id=outlet_id)

    except Outlet.DoesNotExist:
        return Response(
            {
                "error": True,
                "message": "Outlet not found"
            },
            status=status.HTTP_404_NOT_FOUND
        )

    tables = Table.objects.filter(
        outlet=outlet
    ).order_by('table_number')

    response_data = []

    # ---------------------------------------------------
    # CREATE QR DIRECTORY
    # ---------------------------------------------------
    qr_folder = os.path.join(
        settings.MEDIA_ROOT,
        "table_qrs"
    )

    os.makedirs(qr_folder, exist_ok=True)

    # ---------------------------------------------------
    # FONTS
    # ---------------------------------------------------
    try:
        title_font = ImageFont.truetype("arial.ttf", 44)
        subtitle_font = ImageFont.truetype("arial.ttf", 30)
        text_font = ImageFont.truetype("arial.ttf", 26)
        footer_font = ImageFont.truetype("arial.ttf", 22)

    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        footer_font = ImageFont.load_default()

    # ---------------------------------------------------
    # QR CARD GENERATOR
    # ---------------------------------------------------
    def create_qr_card(
        qr_data,
        file_name,
        table_number=None
    ):

        # ---------------------------------------------------
        # GENERATE QR
        # ---------------------------------------------------
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=14,
            border=2
        )

        qr.add_data(qr_data)
        qr.make(fit=True)

        qr_image = qr.make_image(
            fill_color="#111827",
            back_color="white"
        ).convert("RGB")

        qr_image = qr_image.resize((430, 430))

        # ---------------------------------------------------
        # MAIN CANVAS
        # ---------------------------------------------------
        canvas_width = 700
        canvas_height = 1050

        canvas = Image.new(
            "RGB",
            (canvas_width, canvas_height),
            "#eef2ff"
        )

        draw = ImageDraw.Draw(canvas)

        # ---------------------------------------------------
        # MAIN CARD
        # ---------------------------------------------------
        card_margin = 30

        card_x1 = card_margin
        card_y1 = card_margin

        card_x2 = canvas_width - card_margin
        card_y2 = canvas_height - card_margin

        draw.rounded_rectangle(
            (
                card_x1,
                card_y1,
                card_x2,
                card_y2
            ),
            radius=40,
            fill="white",
            outline="#dbeafe",
            width=3
        )

        current_y = 60

        # ---------------------------------------------------
        # TOP HEADER STRIP
        # ---------------------------------------------------
        draw.rounded_rectangle(
            (
                card_x1,
                card_y1,
                card_x2,
                170
            ),
            radius=40,
            fill="#2563eb"
        )

        # ---------------------------------------------------
        # OUTLET LOGO
        # ---------------------------------------------------
        logo_rendered = False

        if outlet.logo:

            try:

                logo_path = os.path.join(
                    settings.MEDIA_ROOT,
                    outlet.logo.name
                )

                if os.path.exists(logo_path):

                    logo = Image.open(
                        logo_path
                    ).convert("RGBA")

                    # -----------------------------------------
                    # REMOVE EXTRA TRANSPARENT/WHITE PADDING
                    # -----------------------------------------
                    bbox = logo.getbbox()

                    if bbox:
                        logo = logo.crop(bbox)

                    # -----------------------------------------
                    # RESIZE LOGO
                    # -----------------------------------------
                    logo_size = 130

                    logo.thumbnail(
                        (logo_size, logo_size),
                        Image.LANCZOS
                    )

                    # -----------------------------------------
                    # CREATE CLEAN CIRCLE CONTAINER
                    # -----------------------------------------
                    container_size = 170

                    logo_container = Image.new(
                        "RGBA",
                        (container_size, container_size),
                        (255, 255, 255, 0)
                    )

                    container_draw = ImageDraw.Draw(
                        logo_container
                    )

                    # soft shadow
                    container_draw.ellipse(
                        (6, 8, container_size-2, container_size),
                        fill=(0, 0, 0, 25)
                    )

                    # white circle
                    container_draw.ellipse(
                        (0, 0, container_size-8, container_size-8),
                        fill=(255, 255, 255, 255)
                    )

                    # -----------------------------------------
                    # CENTER LOGO
                    # -----------------------------------------
                    paste_x = (
                        (container_size - logo.width) // 2
                    ) - 4

                    paste_y = (
                        (container_size - logo.height) // 2
                    ) - 4

                    logo_container.paste(
                        logo,
                        (paste_x, paste_y),
                        logo
                    )

                    # -----------------------------------------
                    # PASTE TO MAIN CANVAS
                    # -----------------------------------------
                    final_x = (
                        canvas_width - container_size
                    ) // 2

                    canvas.paste(
                        logo_container,
                        (final_x, current_y),
                        logo_container
                    )

                    current_y += 185

                    logo_rendered = True

            except Exception as e:
                print("Logo Error:", str(e))
        # ---------------------------------------------------
        # OUTLET NAME
        # ---------------------------------------------------
        outlet_name = outlet.outlet_name

        bbox = draw.textbbox(
            (0, 0),
            outlet_name,
            font=subtitle_font
        )

        text_width = bbox[2] - bbox[0]

        draw.text(
            (
                (canvas_width - text_width) // 2,
                current_y
            ),
            outlet_name,
            fill="#111827",
            font=subtitle_font
        )

        current_y += 60

        # ---------------------------------------------------
        # TABLE NUMBER
        # ---------------------------------------------------
        if table_number:

            table_text = f"Table {table_number}"

            bbox = draw.textbbox(
                (0, 0),
                table_text,
                font=title_font
            )

            text_width = bbox[2] - bbox[0]

            # Pill background
            pill_width = text_width + 60
            pill_height = 65

            pill_x1 = (canvas_width - pill_width) // 2
            pill_y1 = current_y

            pill_x2 = pill_x1 + pill_width
            pill_y2 = pill_y1 + pill_height

            draw.rounded_rectangle(
                (
                    pill_x1,
                    pill_y1,
                    pill_x2,
                    pill_y2
                ),
                radius=40,
                fill="#dbeafe"
            )

            draw.text(
                (
                    (canvas_width - text_width) // 2,
                    current_y + 10
                ),
                table_text,
                fill="#2563eb",
                font=title_font
            )

            current_y += 110

        # ---------------------------------------------------
        # QR CONTAINER
        # ---------------------------------------------------
        qr_box_size = 500

        qr_box_x1 = (canvas_width - qr_box_size) // 2
        qr_box_y1 = current_y

        qr_box_x2 = qr_box_x1 + qr_box_size
        qr_box_y2 = qr_box_y1 + qr_box_size

        # Shadow
        draw.rounded_rectangle(
            (
                qr_box_x1 + 8,
                qr_box_y1 + 10,
                qr_box_x2 + 8,
                qr_box_y2 + 10
            ),
            radius=35,
            fill="#dbeafe"
        )

        # Main box
        draw.rounded_rectangle(
            (
                qr_box_x1,
                qr_box_y1,
                qr_box_x2,
                qr_box_y2
            ),
            radius=35,
            fill="white",
            outline="#bfdbfe",
            width=3
        )

        qr_x = (canvas_width - qr_image.width) // 2
        qr_y = current_y + 35

        canvas.paste(
            qr_image,
            (qr_x, qr_y)
        )

        current_y += qr_box_size + 45

        # ---------------------------------------------------
        # SCAN TEXT
        # ---------------------------------------------------
        scan_text = "Scan QR to Order"

        bbox = draw.textbbox(
            (0, 0),
            scan_text,
            font=text_font
        )

        text_width = bbox[2] - bbox[0]

        draw.text(
            (
                (canvas_width - text_width) // 2,
                current_y
            ),
            scan_text,
            fill="#374151",
            font=text_font
        )

        current_y += 45

        # ---------------------------------------------------
        # SUBTEXT
        # ---------------------------------------------------
        sub_text = "Fast • Secure • Contactless"

        bbox = draw.textbbox(
            (0, 0),
            sub_text,
            font=footer_font
        )

        text_width = bbox[2] - bbox[0]

        draw.text(
            (
                (canvas_width - text_width) // 2,
                current_y
            ),
            sub_text,
            fill="#6b7280",
            font=footer_font
        )

        current_y += 70

        # ---------------------------------------------------
        # FOOTER
        # ---------------------------------------------------
        footer_text = "Powered by Mantra POS"

        bbox = draw.textbbox(
            (0, 0),
            footer_text,
            font=footer_font
        )

        text_width = bbox[2] - bbox[0]

        draw.text(
            (
                (canvas_width - text_width) // 2,
                current_y
            ),
            footer_text,
            fill="#9ca3af",
            font=footer_font
        )

        # ---------------------------------------------------
        # SAVE IMAGE
        # ---------------------------------------------------
        file_path = os.path.join(
            qr_folder,
            file_name
        )

        canvas.save(
            file_path,
            quality=95
        )

        relative_url = (
            f"{settings.MEDIA_URL}table_qrs/{file_name}"
        )

        absolute_url = request.build_absolute_uri(
            relative_url
        )

        return absolute_url

    # ---------------------------------------------------
    # TABLE QR FLOW
    # ---------------------------------------------------
    if tables.exists():

        for table in tables:

            qr_data = f"table_id={table.table_id}"

            file_name = (
                f"table_{table.table_id}.png"
            )

            qr_url = create_qr_card(
                qr_data=qr_data,
                file_name=file_name,
                table_number=table.table_id
            )

            response_data.append({
                "table_number": table.table_number,
                "table_id": table.table_id,
                "location": table.location,
                "qr_data": qr_data,
                "qr_image": qr_url
            })

        return Response({
            "error": False,
            "type": "table_qrs",
            "outlet_id": outlet.id,
            "total_tables": tables.count(),
            "tables": response_data
        })

    # ---------------------------------------------------
    # SINGLE OUTLET QR
    # ---------------------------------------------------
    qr_data = f"outlet_id={outlet.id}"

    file_name = f"outlet_{outlet.id}.png"

    qr_url = create_qr_card(
        qr_data=qr_data,
        file_name=file_name
    )

    return Response({
        "error": False,
        "type": "outlet_qr",
        "outlet_id": outlet.id,
        "qr_data": qr_data,
        "qr_image": qr_url
    })



# {
#   "colors": ["#FF5733", "#2196F3"]
# }



# {
#   "colors": ["#FF5733", "#4CAF50", "#2196F3"]
# }


@swagger_auto_schema(
    method='post',
    operation_description="Add one or more colors to the QR customization's color palette.",
    manual_parameters=[
        openapi.Parameter(
            'outlet_id',
            openapi.IN_PATH,
            description="ID of the Outlet",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["colors"],
        properties={
            "colors": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING, example="#FF5733"),
                description="List of HEX color codes to add"
            )
        }
    ),
    responses={
        200: openapi.Response(description="Colors added successfully."),
        400: openapi.Response(description="Validation error."),
        404: openapi.Response(description="QR Customization not found.")
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_colors_to_palette(request, outlet_id):
    try:
        customization = QRCustomization.objects.get(outlet_id=outlet_id)
    except QRCustomization.DoesNotExist:
        return Response({"error": True, "details": "QR Customization not found."}, status=status.HTTP_404_NOT_FOUND)

    new_colors = request.data.get("colors", [])
    if not isinstance(new_colors, list):
        return Response({"error": True, "details": "Colors must be provided as a list."}, status=status.HTTP_400_BAD_REQUEST)

    if customization.color_palette is None:
        customization.color_palette = []

    customization.color_palette.extend([color for color in new_colors if color not in customization.color_palette])
    customization.save()

    return Response({
        "error": False,
        "details": "Colors added successfully.",
        "color_palette": customization.color_palette
    }, status=status.HTTP_200_OK)









@swagger_auto_schema(
    method='delete',
    operation_description="Remove one or more colors from the QR customization's color palette.",
    manual_parameters=[
        openapi.Parameter(
            'outlet_id',
            openapi.IN_PATH,
            description="ID of the Outlet",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["colors"],
        properties={
            "colors": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING, example="#4CAF50"),
                description="List of HEX color codes to remove"
            )
        }
    ),
    responses={
        200: openapi.Response(description="Colors removed successfully."),
        400: openapi.Response(description="Validation error."),
        404: openapi.Response(description="QR Customization not found.")
    }
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def remove_colors_from_palette(request, outlet_id):
    try:
        customization = QRCustomization.objects.get(outlet_id=outlet_id)
    except QRCustomization.DoesNotExist:
        return Response({"error": True, "details": "QR Customization not found."}, status=status.HTTP_404_NOT_FOUND)

    colors_to_remove = request.data.get("colors", [])
    if not isinstance(colors_to_remove, list):
        return Response({"error": True, "details": "Colors must be provided as a list."}, status=status.HTTP_400_BAD_REQUEST)

    if customization.color_palette is None:
        customization.color_palette = []

    customization.color_palette = [color for color in customization.color_palette if color not in colors_to_remove]
    customization.save()

    return Response({
        "error": False,
        "details": "Colors removed successfully.",
        "color_palette": customization.color_palette
    }, status=status.HTTP_200_OK)












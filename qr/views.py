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
from django.views.decorators.csrf import csrf_exempt

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

        # -----------------------------------------
        # CHECK OUTLET
        # -----------------------------------------
        outlet = get_object_or_404(
            Outlet,
            id=outlet_id
        )

        # -----------------------------------------
        # QUERY PARAMS
        # -----------------------------------------
        is_veg = (
            request.query_params.get(
                'isVeg',
                'true'
            ).lower() == 'true'
        )

        is_nonveg = (
            request.query_params.get(
                'isNonveg',
                'true'
            ).lower() == 'true'
        )

        # -----------------------------------------
        # FETCH PRODUCTS OF OUTLET ONLY
        # -----------------------------------------
        products = Product.objects.filter(
            outlet=outlet
        ).select_related(
            'category'
        ).order_by(
            'category__name',
            'name'
        )

        # -----------------------------------------
        # VEG / NONVEG FILTER
        # -----------------------------------------
        if is_veg and not is_nonveg:

            products = products.filter(
                is_veg=True
            )

        elif not is_veg and is_nonveg:

            products = products.filter(
                is_veg=False
            )

        # -----------------------------------------
        # GROUP BY CATEGORY
        # -----------------------------------------
        category_dict = {}

        for product in products:

            category_id = product.category.id

            category_name = product.category.name

            # Create category group
            if category_id not in category_dict:

                category_dict[category_id] = {
                    "category_id": category_id,
                    "category_name": category_name,
                    "items": []
                }

            # -----------------------------------------
            # FETCH VARIANTS OF CURRENT PRODUCT ONLY
            # -----------------------------------------
            variants_queryset = ProductVariant.objects.filter(
                product_id=product.id
            )

            variants_data = []

            for variant in variants_queryset:

                variants_data.append({

                    "id": variant.id,

                    "name": variant.name,

                    "price": str(variant.price),

                    "is_gst_inclusive": (
                        variant.is_gst_inclusive
                    ),

                    "extra_description": (
                        variant.extra_description
                    ),

                    "created_at": (
                        variant.created_at
                    ),

                    "updated_at": (
                        variant.updated_at
                    ),

                    "is_stock_out": (
                        variant.is_stock_out
                    )
                })

            # -----------------------------------------
            # PRODUCT DATA
            # -----------------------------------------
            product_data = {

                "id": product.id,

                "name": product.name,

                "price": str(product.price),

                "description": (
                    product.description
                ),

                "gst_percentage": (
                    str(product.gst_percentage)
                    if product.gst_percentage
                    else None
                ),

                "is_gst_inclusive": (
                    product.is_gst_inclusive
                ),

                "created_at": (
                    product.created_at
                ),

                "updated_at": (
                    product.updated_at
                ),

                "category": category_name,

                "variants": variants_data,

                "image_url": (
                    request.build_absolute_uri(
                        product.image.url
                    )
                    if product.image
                    else None
                ),

                "is_veg": (
                    product.is_veg
                ),

                "is_stock_out": (
                    product.is_stock_out
                )
            }

            # -----------------------------------------
            # ADD PRODUCT TO CATEGORY
            # -----------------------------------------
            category_dict[
                category_id
            ]["items"].append(
                product_data
            )

        # -----------------------------------------
        # FINAL RESPONSE
        # -----------------------------------------
        response_data = list(
            category_dict.values()
        )

        return Response({
            "error": False,
            "details": (
                "Products fetched successfully"
            ),
            "sequence": 3,
            "categories": response_data

        })

    except Exception as e:
        return Response({
            "error": True,
            "details": (
                f"An error occurred: {str(e)}"
            )
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

        # 🔥 GET SINGLE SPECIAL MENU
        menu = SpecialMenu.objects.filter(
            outlet_id=outlet_id
        ).first()

        if not menu:

            return Response(
                {
                    "error": True,
                    "detail": (
                        "No special menus found for this outlet."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    except Exception:

        return Response(
            {
                "error": True,
                "detail": "Outlet not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # 🔥 SINGLE OBJECT SERIALIZER
    serializer = SpecialMenuSerializer(menu)

    return Response(
        {
            "error": False,

            # 🔥 OBJECT INSTEAD OF ARRAY
            "special_menus": serializer.data
        },
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
            "qr_logo": request.build_absolute_uri(outlet.logo.url) if outlet.logo else None,
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
def create_special_menu(request, outlet_id):

    try:

        # 🔥 GET OUTLET
        try:
            outlet = Outlet.objects.get(id=outlet_id)

        except Outlet.DoesNotExist:
            return Response({
                "error": True,
                "detail": "Outlet not found."
            }, status=status.HTTP_404_NOT_FOUND)

        name = request.data.get("name")

        product_ids = request.data.get(
            "product_ids",
            []
        )

        if not name:
            return Response({
                "error": True,
                "detail": "Menu name is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 🔥 MAX 5 PRODUCTS CHECK
        if len(product_ids) > 5:
            return Response({
                "error": True,
                "detail": "Maximum 5 products are allowed in special menu."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Fetch outlet products only
        products = Product.objects.filter(
            outlet=outlet,
            id__in=product_ids
        )

        # ==========================================
        # CHECK IF MENU EXISTS
        # ==========================================
        special_menu = SpecialMenu.objects.filter(
            outlet=outlet,
            name=name
        ).first()

        # ==========================================
        # UPDATE EXISTING MENU
        # ==========================================
        if special_menu:

            special_menu.products.set(products)

            message = "Special menu updated successfully."

            status_code = status.HTTP_200_OK

        # ==========================================
        # CREATE NEW MENU
        # ==========================================
        else:

            special_menu = SpecialMenu.objects.create(
                outlet=outlet,
                name=name
            )

            special_menu.products.set(products)

            message = "Special menu created successfully."

            status_code = status.HTTP_201_CREATED

        return Response({
            "error": False,

            "detail": message,

            "menu": {
                "id": special_menu.id,

                "name": special_menu.name,

                "outlet": {
                    "id": outlet.id,
                    "name": outlet.outlet_name
                },

                "products": [
                    {
                        "id": product.id,
                        "name": product.name,
                        "price": str(product.price),
                        "description": product.description,
                        "is_veg": product.is_veg,
                        "is_stock_out": product.is_stock_out,
                    }
                    for product in special_menu.products.all()
                ]
            }

        }, status=status_code)

    except Exception as e:

        return Response({
            "error": True,
            "detail": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def generate_table_qrs(request, outlet_id):

    try:
        outlet = Outlet.objects.get(id=outlet_id)

    except Outlet.DoesNotExist:
        return Response(
            {"error": True, "message": "Outlet not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    tables = Table.objects.filter(outlet=outlet).order_by('table_number')

    response_data = []

    # ---------------------------------------------------
    # CREATE QR DIRECTORY
    # ---------------------------------------------------
    qr_folder = os.path.join(settings.MEDIA_ROOT, "table_qrs")
    os.makedirs(qr_folder, exist_ok=True)

    # ---------------------------------------------------
    # FONTS
    # ---------------------------------------------------
    try:
        outlet_font  = ImageFont.truetype("arial.ttf", 40)   # outlet name
        table_font   = ImageFont.truetype("arial.ttf", 48)   # table number
        scan_font    = ImageFont.truetype("arial.ttf", 46)   # scan to order  ← BIG
        footer_font  = ImageFont.truetype("arial.ttf", 24)   # powered by

    except:
        outlet_font  = ImageFont.load_default()
        table_font   = ImageFont.load_default()
        scan_font    = ImageFont.load_default()
        footer_font  = ImageFont.load_default()

    # ---------------------------------------------------
    # QR CARD GENERATOR
    # ---------------------------------------------------
    def create_qr_card(qr_data, file_name, table_number=None):

        # ── QR CODE ──────────────────────────────────────
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=12,
            border=2
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        qr_image = qr.make_image(
            fill_color="#111827",
            back_color="white"
        ).convert("RGB")

        qr_image = qr_image.resize((400, 400))

        # ── CANVAS ───────────────────────────────────────
        canvas_width  = 600
        canvas_height = 1060      # tall enough for all elements

        canvas = Image.new("RGB", (canvas_width, canvas_height), "#f1f5f9")
        draw   = ImageDraw.Draw(canvas)

        # ── WHITE CARD ───────────────────────────────────
        cm = 22   # card margin
        draw.rounded_rectangle(
            (cm, cm, canvas_width - cm, canvas_height - cm),
            radius=30,
            fill="white",
            outline="#e2e8f0",
            width=2
        )

        current_y = 55

        # ── OUTLET LOGO ──────────────────────────────────
        logo_rendered = False

        if outlet.logo:
            try:
                logo_path = os.path.join(settings.MEDIA_ROOT, outlet.logo.name)

                if os.path.exists(logo_path):
                    logo = Image.open(logo_path).convert("RGBA")

                    # crop transparent padding
                    bbox = logo.getbbox()
                    if bbox:
                        logo = logo.crop(bbox)

                    # fit inside circle
                    logo_size = 118
                    logo.thumbnail((logo_size, logo_size), Image.LANCZOS)

                    container_size = 148

                    # ── clean white circle with border ──
                    circle_img  = Image.new("RGBA", (container_size, container_size), (0, 0, 0, 0))
                    circle_draw = ImageDraw.Draw(circle_img)

                    # border ring
                    circle_draw.ellipse(
                        (0, 0, container_size - 1, container_size - 1),
                        fill=(226, 232, 240, 255)   # #e2e8f0
                    )

                    # white fill
                    border = 3
                    circle_draw.ellipse(
                        (border, border, container_size - border - 1, container_size - border - 1),
                        fill=(255, 255, 255, 255)
                    )

                    # ── circular mask for logo ──────────
                    inner  = container_size - border * 2 - 1
                    mask   = Image.new("L", (inner, inner), 0)
                    ImageDraw.Draw(mask).ellipse((0, 0, inner - 1, inner - 1), fill=255)

                    logo_canvas = Image.new("RGBA", (inner, inner), (255, 255, 255, 255))
                    lx = (inner - logo.width)  // 2
                    ly = (inner - logo.height) // 2
                    logo_canvas.paste(logo, (lx, ly), logo)
                    logo_canvas.putalpha(mask)

                    circle_img.paste(logo_canvas, (border, border), logo_canvas)

                    paste_x = (canvas_width - container_size) // 2
                    canvas.paste(circle_img, (paste_x, current_y), circle_img)

                    current_y  += container_size + 20
                    logo_rendered = True

            except Exception as e:
                print("Logo Error:", str(e))

        # ── OUTLET NAME ──────────────────────────────────
        outlet_name = outlet.outlet_name
        bbox        = draw.textbbox((0, 0), outlet_name, font=outlet_font)
        text_width  = bbox[2] - bbox[0]

        draw.text(
            ((canvas_width - text_width) // 2, current_y),
            outlet_name,
            fill="#1e293b",
            font=outlet_font
        )

        current_y += 55

        # ── DIVIDER ──────────────────────────────────────
        div_margin = 100
        draw.line(
            (div_margin, current_y, canvas_width - div_margin, current_y),
            fill="#e2e8f0",
            width=2
        )

        current_y += 28

        # ── TABLE NUMBER PILL ────────────────────────────
        if table_number:
            table_text = f"Table  {table_number}"
            bbox       = draw.textbbox((0, 0), table_text, font=table_font)
            tw         = bbox[2] - bbox[0]
            th         = bbox[3] - bbox[1]

            pill_w  = tw + 80
            pill_h  = th + 30
            pill_x1 = (canvas_width - pill_w) // 2
            pill_y1 = current_y

            draw.rounded_rectangle(
                (pill_x1, pill_y1, pill_x1 + pill_w, pill_y1 + pill_h),
                radius=pill_h // 2,
                fill="#eff6ff",
                outline="#bfdbfe",
                width=2
            )

            draw.text(
                ((canvas_width - tw) // 2, pill_y1 + 14),
                table_text,
                fill="#2563eb",
                font=table_font
            )

            current_y += pill_h + 32

        # ── QR IMAGE BOX ─────────────────────────────────
        qr_pad   = 20
        qr_box_w = qr_image.width  + qr_pad * 2
        qr_box_h = qr_image.height + qr_pad * 2
        qr_box_x = (canvas_width - qr_box_w) // 2

        # shadow
        draw.rounded_rectangle(
            (qr_box_x + 5, current_y + 7, qr_box_x + qr_box_w + 5, current_y + qr_box_h + 7),
            radius=18,
            fill="#e2e8f0"
        )

        # box
        draw.rounded_rectangle(
            (qr_box_x, current_y, qr_box_x + qr_box_w, current_y + qr_box_h),
            radius=18,
            fill="white",
            outline="#e2e8f0",
            width=2
        )

        canvas.paste(qr_image, (qr_box_x + qr_pad, current_y + qr_pad))

        current_y += qr_box_h + 38

        # ── SCAN QR TO ORDER  (big, bold-ish) ────────────
        scan_text  = "Scan QR to Order"
        bbox       = draw.textbbox((0, 0), scan_text, font=scan_font)
        text_width = bbox[2] - bbox[0]

        draw.text(
            ((canvas_width - text_width) // 2, current_y),
            scan_text,
            fill="#111827",
            font=scan_font
        )

        current_y += 58

        # ── POWERED BY MANTRA POS ────────────────────────
        footer_text = "Powered by Mantra POS"
        bbox        = draw.textbbox((0, 0), footer_text, font=footer_font)
        text_width  = bbox[2] - bbox[0]

        draw.text(
            ((canvas_width - text_width) // 2, current_y),
            footer_text,
            fill="#94a3b8",
            font=footer_font
        )

        # ── SAVE ─────────────────────────────────────────
        file_path = os.path.join(qr_folder, file_name)
        canvas.save(file_path, quality=95)

        relative_url = f"{settings.MEDIA_URL}table_qrs/{file_name}"
        return request.build_absolute_uri(relative_url)

    # ---------------------------------------------------
    # TABLE QR FLOW
    # ---------------------------------------------------
    if tables.exists():

        for table in tables:

            qr_data   = f"https://qr.mantrapos.com/{outlet.id}/{table.id}"
            file_name = f"table_{table.id}.png"

            qr_url = create_qr_card(
                qr_data=qr_data,
                file_name=file_name,
                table_number=table.table_id
            )

            response_data.append({
                "table_number": table.table_number,
                "table_id":     table.table_id,
                "location":     table.location,
                "qr_data":      qr_data,
                "qr_image":     qr_url
            })

        return Response({
            "error":        False,
            "type":         "table_qrs",
            "outlet_id":    outlet.id,
            "total_tables": tables.count(),
            "tables":       response_data
        })

    # ---------------------------------------------------
    # SINGLE OUTLET QR
    # ---------------------------------------------------
    qr_data   = f"https://qr.mantrapos.com/{outlet.id}"
    file_name = f"outlet_{outlet.id}.png"

    qr_url = create_qr_card(qr_data=qr_data, file_name=file_name)

    return Response({
        "error":     False,
        "type":      "outlet_qr",
        "outlet_id": outlet.id,
        "qr_data":   qr_data,
        "qr_image":  qr_url
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










@swagger_auto_schema(
    method='get',
    operation_description="Get QR customization details for a specific outlet.",
    manual_parameters=[
        openapi.Parameter(
            'outlet_id',
            openapi.IN_PATH,
            description="ID of the outlet",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="QR customization fetched successfully",
            examples={
                "application/json": {
                    "error": False,
                    "detail": "QR customization fetched successfully.",
                    "customization": {
                        "id": 1,
                        "outlet": {
                            "id": 5,
                            "name": "Mantra Cafe"
                        },
                        "qr_tagline": "Scan & Order",
                        "qr_logo": "https://yourdomain.com/media/qr_logos/logo.png",
                        "theme_color": "#FF5733",
                        "color_palette": [
                            "#FF5733",
                            "#FFFFFF",
                            "#000000"
                        ]
                    }
                }
            }
        ),

        404: openapi.Response(
            description="Outlet not found",
            examples={
                "application/json": {
                    "error": True,
                    "detail": "Outlet not found."
                }
            }
        ),

        500: openapi.Response(
            description="Internal server error",
            examples={
                "application/json": {
                    "error": True,
                    "detail": "Something went wrong."
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_qr_customization(request, outlet_id):
    try:

        outlet = Outlet.objects.get(id=outlet_id)
        qr_customization = QRCustomization.objects.filter(
            outlet=outlet
        ).first()

        # If no customization exists
        if not qr_customization:
            return Response({
                "error": False,
                "detail": "QR customization not found.",
                "customization": None
            }, status=status.HTTP_200_OK)

        return Response({
            "error": False,
            "detail": "QR customization fetched successfully.",
            "customization": {
                "id": qr_customization.id,

                "outlet": {
                    "id": outlet.id,
                    "name": outlet.outlet_name
                },

                "qr_tagline": qr_customization.qr_tagline,

                "qr_logo": (
                    request.build_absolute_uri(
                        qr_customization.qr_logo.url
                    )
                    if qr_customization.qr_logo
                    else None
                ),

                "theme_color": qr_customization.theme_color,

                "color_palette": (
                    qr_customization.color_palette
                    if qr_customization.color_palette
                    else []
                )
            }
        }, status=status.HTTP_200_OK)

    except Outlet.DoesNotExist:
        return Response({
            "error": True,
            "detail": "Outlet not found."
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            "error": True,
            "detail": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from django.shortcuts import render

import random
import string
import base64
import json

from decimal import Decimal

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework import status

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
    FCMToken
)

from .models import (
    QRCustomization
)

from .serializers import (
    ProductSerializer,
    ProductVariantSerializer,
    OrderItemSerializer,
    OrderSerializer,
    CouponSerializer,
    RazorpayCredentialSerializer,
    OutletSerializer
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
    
    
    
    
    
    

@swagger_auto_schema(
    method='get',
    operation_summary="Get random products",
    operation_description="Fetch up to three random products from the database along with their variants. If less than three products exist, it returns the available products.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "error": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Indicates success or failure"),
                "details": openapi.Schema(type=openapi.TYPE_STRING, description="Message describing the result"),
                "products": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="Product ID"),
                            "name": openapi.Schema(type=openapi.TYPE_STRING, description="Product name"),
                            "price": openapi.Schema(type=openapi.TYPE_STRING, description="Product price"),
                            "is_veg": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Indicates if the product is veg"),
                            "variants": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="Variant ID"),
                                        "name": openapi.Schema(type=openapi.TYPE_STRING, description="Variant name"),
                                        "price": openapi.Schema(type=openapi.TYPE_STRING, description="Variant price"),
                                    }
                                ),
                                description="List of product variants"
                            ),
                        }
                    ),
                    description="List of random products with variants"
                )
            }
        ),
        500: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "error": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Indicates failure"),
                "details": openapi.Schema(type=openapi.TYPE_STRING, description="Error message")
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def random_products(request, outlet_id):
    try:
        # Check if the outlet exists
        outlet = Outlet.objects.filter(id=outlet_id).first()
        if not outlet:
            return Response({
                "error": True,
                "details": "Outlet not found."
            }, status=status.HTTP_404_NOT_FOUND)

        # Get all products for the specified outlet
        products = list(Product.objects.filter(outlet=outlet).prefetch_related('variants'))

        # Shuffle the products list to randomize the selection
        random.shuffle(products)

        # If the number of products is less than 3, return only one product
        if len(products) < 3:
            selected_products = products[:1]
        else:
            selected_products = products[:3]

        # Serialize the selected products along with their variants
        product_list = []
        for product in selected_products:
            product_data = ProductSerializer(product).data
            variants = product.variants.all()
            variant_data = ProductVariantSerializer(variants, many=True).data
            product_data['variants'] = variant_data
            product_list.append(product_data)

        return Response({
            "error": False,
            "details": "Random products fetched successfully.",
            "products": product_list
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "error": True,
            "details": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        
        





@swagger_auto_schema(
    method='get',
    operation_summary="Get banners",
    operation_description="Fetch a list of banner images with their respective redirect URLs.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "error": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Indicates success or failure"),
                "details": openapi.Schema(type=openapi.TYPE_STRING, description="Message describing the result"),
                "banners": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "image_url": openapi.Schema(type=openapi.TYPE_STRING, description="URL of the banner image"),
                            "redirect_url": openapi.Schema(type=openapi.TYPE_STRING, description="URL to redirect on banner click")
                        }
                    ),
                    description="List of banner objects"
                )
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_banners(request,outlet_id):
    try:
        banners = [
            {
                "image_url": "https://images.pexels.com/photos/12935078/pexels-photo-12935078.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
                "redirect_url": "https://mantrapos.com/"
            },
            {
                "image_url": "https://images.pexels.com/photos/4921260/pexels-photo-4921260.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
                "redirect_url": "https://mantrapos.com/"
            }
        ]

        return Response({
            "error": False,
            "details": "Active Banners fetched successfully.",
            "banners": banners
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "error": True,
            "details": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)









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






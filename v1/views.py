import random
import string
import math

from datetime import datetime

from django.shortcuts import get_object_or_404,render
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.utils.timezone import localtime
from django.utils.timezone import now
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.db.models import Q, Min

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from firebase_admin import messaging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound



from .models import (
    Company,
    Outlet,
    OutletAccess,
    Employee,
    Plan,
    PlanAssignment,
    Product,
    ProductVariant,
    Menu,
    Category,
    StockRequest, 
    FCMToken,
    EmployeeCredentials,
    Order,
    OrderItem,
    Customer,
    RefundNote,
    PrinterConfig
)

from .serializers import (
    OutletSerializer,
    EmployeeCreateSerializer,
    ProductSerializer,
    ProductVariantSerializer,
    MenuSerializer,
    MenuListSerializer,
    MenuDetailSerializer,
    CategorySerializer,
    EmployeeSerializer,
    StockRequestListSerializer,
    ApproveStockRequestSerializer,
    EmployeeListSerializer,
    EmployeePermissionsUpdateSerializer,
    EmployeeCredentialsSerializer,
    ManageEmployeeCredentialsSerializer,
    OrderSerializer,
    OrderDetailSerializer,
    OrderBillSerializer,
    RefundNoteSerializer
)


User = get_user_model()




@swagger_auto_schema(
    method='post',
    operation_description="Create a new outlet for a company.",
    request_body=OutletSerializer,
    responses={
        201: "Outlet created successfully.",
        400: "Bad request.",
        401: "Unauthorized.",
        403: "Forbidden.",
        404: "Company not found."
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_outlet(request, company_id,user_id):
    # Manually handle token authentication
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate the token and retrieve the user
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:  # Check if the token belongs to the user ID provided in the URL
            return Response({"error":True,"detail": "Token is not valid. Invalid Authentication Header"}, status=status.HTTP_403_FORBIDDEN)
        
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

   
    # Verify if the requesting user has the "manager" role
    try:
        employee_record = Employee.objects.get(user=requesting_user)
        if employee_record.role != 'manager':
            return Response({"error":True, "detail":"Only a manager can create outlets"}, status=status.HTTP_403_FORBIDDEN)
    except Employee.DoesNotExist:
        return Response({"error":True, "detail": "User is not an employee or manager"}, status=status.HTTP_403_FORBIDDEN)
    
    
    company = get_object_or_404(Company, id=company_id)
    outlet_data = request.data
    outlet_data['company'] = company.id
    serializer = OutletSerializer(data=outlet_data)
    
    if serializer.is_valid():
        serializer.save()
        return Response({"error":False, "detail":"Outlet Added Successfully", **serializer.data}, status=status.HTTP_201_CREATED)
    return Response({"error":True,  **serializer.errors}, status=status.HTTP_400_BAD_REQUEST)








@swagger_auto_schema(
    method='post',
    operation_description="Grant or update access permissions for a user on an outlet.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'permissions': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description="Permissions granted to the user for this outlet.",
                properties={
                    'view': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Permission to view the outlet."),
                    'edit': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Permission to edit the outlet."),
                    'delete': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Permission to delete the outlet.")
                }
            ),
        },
        required=['permissions']
    ),
    responses={
        201: openapi.Response(
            description="Access granted successfully.",
            examples={
                'application/json': {
                    "error": False,
                    "detail": "Access granted successfully.",
                    "permissions": {
                        "view": True,
                        "edit": False,
                        "delete": False
                    }
                }
            }
        ),
        200: openapi.Response(
            description="Access updated successfully.",
            examples={
                'application/json': {
                    "error": False,
                    "detail": "Access updated successfully.",
                    "permissions": {
                        "view": True,
                        "edit": True,
                        "delete": False
                    }
                }
            }
        ),
        401: "Authorization token is missing or invalid.",
        403: "Only managers can grant or update access.",
        404: "User or outlet not found."
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def grant_outlet_access(request, outlet_id, user_id,manager_id):
    # Manually handle token authentication
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate the token and retrieve the user
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != manager_id:  # Check if the token belongs to the user ID provided in the URL
            return Response({"error":True,"detail": "Token is not valid. Invalid Authentication Header"}, status=status.HTTP_403_FORBIDDEN)
        
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

   
    # Verify if the requesting user has the "manager" role
    try:
        employee_record = Employee.objects.get(user=requesting_user)
        if employee_record.role != 'manager':
            return Response({"error":True, "detail":"Only a manager can grant access"}, status=status.HTTP_403_FORBIDDEN)
    except Employee.DoesNotExist:
        return Response({"error":True, "detail": "User is not an employee or manager"}, status=status.HTTP_403_FORBIDDEN)
    
    
    outlet = get_object_or_404(Outlet, id=outlet_id)
    user = get_object_or_404(get_user_model(), id=user_id)

    permissions = request.data.get('permissions', {})

    outlet_access, created = OutletAccess.objects.update_or_create(
        user=user,
        outlet=outlet,
        defaults={'permissions': permissions}
    )

    if created:
        return Response({"error":False, "detail": "Access granted successfully.", "permissions": permissions}, status=status.HTTP_201_CREATED)
    else:
        return Response({"error":False, "detail": "Access updated successfully.", "permissions": permissions}, status=status.HTTP_200_OK)
    
    
    





@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('company_id', openapi.IN_PATH, description="Company ID", type=openapi.TYPE_INTEGER)
    ],
    responses={200: OutletSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])  # Adjust as per your authentication
def list_company_outlets(request, company_id, user_id):
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:
            return Response({"error": True, "detail": "Token is not valid. Invalid Authentication Header"}, status=status.HTTP_403_FORBIDDEN)
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        employee_record = Employee.objects.get(user=requesting_user)
        if employee_record.role != 'manager':
            return Response({"error": True, "detail": "Only a manager can get list of all outlets of a company"}, status=status.HTTP_403_FORBIDDEN)
    except Employee.DoesNotExist:
        return Response({"error": True, "detail": "User is not an employee or manager"}, status=status.HTTP_403_FORBIDDEN)

    # Fetch outlets
    outlets = Outlet.objects.filter(company_id=company_id)
    total_outlets = outlets.count()
    active_outlets = outlets.filter(is_active=True).count()
    inactive_outlets = outlets.filter(is_active=False).count()

    serializer = OutletSerializer(outlets, many=True)
    
    return Response({
        "error": False,
        "outlets": serializer.data,
        "total_outlets": total_outlets,
        "total_active_outlets": active_outlets,
        "total_inactive_outlets": inactive_outlets
    }, status=status.HTTP_200_OK)





@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('outlet_id', openapi.IN_PATH, description="Outlet ID", type=openapi.TYPE_INTEGER)
    ],
    responses={200: OutletSerializer()}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_outlet_detail(request, outlet_id,user_id):
    # Manually handle token authentication
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate the token and retrieve the user
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:  # Check if the token belongs to the user ID provided in the URL
            return Response({"error":True,"detail": "Token is not valid. Invalid Authentication Header"}, status=status.HTTP_403_FORBIDDEN)
        
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

   
    # Verify if the requesting user has the "manager" role
    try:
        employee_record = Employee.objects.get(user=requesting_user)
        if employee_record.role != 'manager':
            return Response({"error":True, "detail":"Only a manager can get specific outlet details"}, status=status.HTTP_403_FORBIDDEN)
    except Employee.DoesNotExist:
        return Response({"error":True, "detail": "User is not an employee or manager"}, status=status.HTTP_403_FORBIDDEN)
    
    
    outlet = get_object_or_404(Outlet, id=outlet_id)
    serializer = OutletSerializer(outlet)
    return Response({"error": False, "outlet": serializer.data})






@swagger_auto_schema(
    method='put',
    manual_parameters=[
        openapi.Parameter('outlet_id', openapi.IN_PATH, description="Outlet ID", type=openapi.TYPE_INTEGER),
        openapi.Parameter('Authorization', openapi.IN_HEADER, description="User token", type=openapi.TYPE_STRING)
    ],
    request_body=OutletSerializer,
    responses={200: OutletSerializer()}
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_outlet(request, outlet_id,user_id):
    # Manually handle token authentication
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate the token and retrieve the user
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:  # Check if the token belongs to the user ID provided in the URL
            return Response({"error":True,"detail": "Token is not valid. Invalid Authentication Header"}, status=status.HTTP_403_FORBIDDEN)
        
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

   
    # Verify if the requesting user has the "manager" role
    try:
        employee_record = Employee.objects.get(user=requesting_user)
        if employee_record.role != 'manager':
            return Response({"error":True, "detail":"Only a manager can update outlets"}, status=status.HTTP_403_FORBIDDEN)
    except Employee.DoesNotExist:
        return Response({"error":True, "detail": "User is not an employee or manager"}, status=status.HTTP_403_FORBIDDEN)
    
    
    outlet = get_object_or_404(Outlet, id=outlet_id)
    serializer = OutletSerializer(outlet, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response({"error": False, "detail": "Outlet updated successfully", "outlet": serializer.data})
    return Response({"error": True, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)









@swagger_auto_schema(
    method='delete',
    manual_parameters=[
        openapi.Parameter('outlet_id', openapi.IN_PATH, description="Outlet ID", type=openapi.TYPE_INTEGER),
        openapi.Parameter('Authorization', openapi.IN_HEADER, description="User token", type=openapi.TYPE_STRING)
    ],
    responses={200: openapi.Response(description="Outlet deleted successfully")}
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_outlet(request, outlet_id,user_id):
    # Manually handle token authentication
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate the token and retrieve the user
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:  # Check if the token belongs to the user ID provided in the URL
            return Response({"error":True,"detail": "Token is not valid. Invalid Authentication Header"}, status=status.HTTP_403_FORBIDDEN)
        
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

   
    # Verify if the requesting user has the "manager" role
    try:
        employee_record = Employee.objects.get(user=requesting_user)
        if employee_record.role != 'manager':
            return Response({"error":True, "detail":"Only a manager can delete outlets"}, status=status.HTTP_403_FORBIDDEN)
    except Employee.DoesNotExist:
        return Response({"error":True, "detail": "User is not an employee or manager"}, status=status.HTTP_403_FORBIDDEN)
    
    
    outlet = get_object_or_404(Outlet, id=outlet_id)
    outlet.delete()
    return Response({"error": False, "detail": "Outlet deleted successfully"}, status=status.HTTP_200_OK)










## Sample Body
# {
#   "first_name": "Rahul",
#   "last_name": "Sharma",
#   "email": "rahul.sharma@example.com",
#   "phone_number": "9876543210",
#   "address": "123 MG Road, Bengaluru",
#   "date_of_birth": "1995-06-15",
#   "role": "store_admin",
#   "permissions": {
#     "can_add_product": true,
#     "can_view_reports": true,
#     "can_manage_orders": false
#   }
# }



@swagger_auto_schema(
    method='post',
    operation_description="Create a new employee.",
    request_body=EmployeeCreateSerializer,
    responses={
        201: "Employee created successfully.",
        400: "Bad request.",
        401: "Unauthorized.",
        403: "Forbidden.",
        404: "Company not found."
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_employee(request, user_id):
    # Manually handle token authentication
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate the token and retrieve the user
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:  # Check if the token belongs to the user ID provided in the URL
            return Response({"error":True,"detail": "Token is not valid. Invalid Authentication Header"}, status=status.HTTP_403_FORBIDDEN)
        
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

   
    # Verify if the requesting user has the "manager" role
    try:
        employee_record = Employee.objects.get(user=requesting_user)
        if employee_record.role != 'manager':
            return Response({"error":True, "detail":"Only a manager can add employees"}, status=status.HTTP_403_FORBIDDEN)
    except Employee.DoesNotExist:
        return Response({"error":True, "detail": "User is not an employee or manager"}, status=status.HTTP_403_FORBIDDEN)

    # Serialize and validate request data
    serializer = EmployeeCreateSerializer(data=request.data)
    if serializer.is_valid():
        validated_data = serializer.validated_data

        # Get company from the requesting user
        company = requesting_user.company

        # Create the user and employee entry
        new_user = serializer.create_employee_user(validated_data, company=company)

        # Add the new employee in Employee model
        employee = Employee.objects.create(
            company=company,
            user=new_user,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            phone_number=validated_data.get('phone_number'),
            profile_image=validated_data.get('profile_image'),
            address=validated_data.get('address'),
            date_of_birth=validated_data.get('date_of_birth'),
            role=validated_data['role'],
            is_active=True,
            permissions=validated_data.get('permissions', {})
        )

        return Response({
            "error": False,
            "detail": "Employee created successfully.",
            "username": new_user.username,
            "employee_code": employee.employee_code,
            "email": new_user.email
        }, status=status.HTTP_201_CREATED)
    
    return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)









@swagger_auto_schema(
    method='post',
    operation_description="Add a new product.",
    request_body=ProductSerializer,
    responses={
        201: "Product added successfully.",
        400: "Bad request.",
        401: "Unauthorized."
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_product(request,user_id):
    # Authenticate the request
     # Manually handle token authentication
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate the token and retrieve the user
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:  # Check if the token belongs to the user ID provided in the URL
            return Response({"error":True,"detail": "Token is not valid. Invalid Authentication Header"}, status=status.HTTP_403_FORBIDDEN)
        
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate the request data with the serializer
    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        # Save the product data and return a success response
        serializer.save()
        return Response({
            "error": False,
            "detail": "Product added successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
    
    # Return errors if the data is invalid
    return Response({"error": True, "detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)









@swagger_auto_schema(
    method='post',
    operation_description="Add a new product variant.",
    request_body=ProductVariantSerializer,
    responses={
        201: "Product variant added successfully.",
        400: "Bad request.",
        401: "Unauthorized."
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_product_variant(request,user_id):
    # Authenticate the request
     # Manually handle token authentication
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate the token and retrieve the user
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:  # Check if the token belongs to the user ID provided in the URL
            return Response({"error":True,"detail": "Token is not valid. Invalid Authentication Header"}, status=status.HTTP_403_FORBIDDEN)
        
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate the request data with the serializer
    serializer = ProductVariantSerializer(data=request.data)
    if serializer.is_valid():
        # Save the product variant data and return a success response
        serializer.save()
        return Response({
            "error": False,
            "detail": "Product variant added successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
    
    # Return errors if the data is invalid
    return Response({"error": True, "detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)













@swagger_auto_schema(
    method='post',
    operation_description="Add a new product with its variants in a single request.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "product": openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "name": openapi.Schema(type=openapi.TYPE_STRING, description="Product name"),
                    "price": openapi.Schema(type=openapi.TYPE_NUMBER, description="Base product price"),
                    "image": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description="Product image URL"),
                    "description": openapi.Schema(type=openapi.TYPE_STRING, description="Product description"),
                    "outlet": openapi.Schema(type=openapi.TYPE_INTEGER, description="Outlet ID"),
                    "is_gst_inclusive": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="GST inclusive or not"),
                    "category": openapi.Schema(type=openapi.TYPE_INTEGER, description="Category ID"),
                    "is_veg": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Is the product vegetarian")
                },
                required=["name", "price", "outlet", "category"]
            ),
            "variants": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "price": openapi.Schema(type=openapi.TYPE_NUMBER, description="Variant price"),
                        "is_gst_inclusive": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="GST inclusive for variant"),
                        "extra_description": openapi.Schema(type=openapi.TYPE_STRING, description="Extra details for the variant")
                    },
                    required=["price"]
                )
            )
        },
        required=["product"]
    ),
    responses={
        201: "Product with variants added successfully.",
        400: "Bad request.",
        401: "Unauthorized."
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_product_with_variants(request, user_id):
    # Authenticate the request
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:
            return Response({"error": True, "detail": "Token is not valid. Invalid Authentication Header"}, status=status.HTTP_403_FORBIDDEN)
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    # Extract product and variants from request
    product_data = request.data.get("product")
    variants_data = request.data.get("variants", [])

    if not product_data:
        return Response({"error": True, "detail": "Product data is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Validate and create product
    product_serializer = ProductSerializer(data=product_data)
    if not product_serializer.is_valid():
        return Response({"error": True, "detail": product_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    product = product_serializer.save()

    # Validate and create variants
    created_variants = []
    for variant in variants_data:
        variant["product"] = product.id  # attach product FK
        variant_serializer = ProductVariantSerializer(data=variant)
        if variant_serializer.is_valid():
            created_variants.append(variant_serializer.save())
        else:
            return Response({"error": True, "detail": variant_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        "error": False,
        "detail": "Product with variants added successfully",
        "product": product_serializer.data,
        "variants": ProductVariantSerializer(created_variants, many=True).data
    }, status=status.HTTP_201_CREATED)





@swagger_auto_schema(
    method='put',
    operation_description="Edit an existing product.",
    request_body=ProductSerializer,
    responses={
        200: "Product updated successfully.",
        400: "Bad request.",
        401: "Unauthorized.",
        404: "Product not found."
    }
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def edit_product(request, user_id, product_id):
    # Token authentication
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:
            return Response({"error": True, "detail": "Token is not valid"}, status=status.HTTP_403_FORBIDDEN)
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    # Get product
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({"error": True, "detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

    # Update product
    serializer = ProductSerializer(product, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"error": False, "detail": "Product updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
    return Response({"error": True, "detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)









@swagger_auto_schema(
    method='delete',
    operation_description="Delete a product by ID.",
    responses={
        204: "Product deleted successfully.",
        401: "Unauthorized.",
        404: "Product not found."
    }
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_product(request, user_id, product_id):
    # Token authentication
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:
            return Response({"error": True, "detail": "Token is not valid"}, status=status.HTTP_403_FORBIDDEN)
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    # Delete product
    try:
        product = Product.objects.get(id=product_id)
        product.delete()
        return Response({"error": False, "detail": "Product deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    except Product.DoesNotExist:
        return Response({"error": True, "detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)













@swagger_auto_schema(
    method='put',
    operation_description="Edit an existing product variant.",
    request_body=ProductVariantSerializer,
    responses={
        200: "Product variant updated successfully.",
        400: "Bad request.",
        401: "Unauthorized.",
        404: "Product variant not found."
    }
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def edit_product_variant(request, user_id, variant_id):
    # Token authentication
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:
            return Response({"error": True, "detail": "Token is not valid"}, status=status.HTTP_403_FORBIDDEN)
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    # Get variant
    try:
        variant = ProductVariant.objects.get(id=variant_id)
    except ProductVariant.DoesNotExist:
        return Response({"error": True, "detail": "Product variant not found"}, status=status.HTTP_404_NOT_FOUND)

    # Update variant
    serializer = ProductVariantSerializer(variant, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"error": False, "detail": "Product variant updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
    return Response({"error": True, "detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)










@swagger_auto_schema(
    method='delete',
    operation_description="Delete a product variant by ID.",
    responses={
        204: "Product variant deleted successfully.",
        401: "Unauthorized.",
        404: "Product variant not found."
    }
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_product_variant(request, user_id, variant_id):
    # Token authentication
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:
            return Response({"error": True, "detail": "Token is not valid"}, status=status.HTTP_403_FORBIDDEN)
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    # Delete variant
    try:
        variant = ProductVariant.objects.get(id=variant_id)
        variant.delete()
        return Response({"error": False, "detail": "Product variant deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    except ProductVariant.DoesNotExist:
        return Response({"error": True, "detail": "Product variant not found"}, status=status.HTTP_404_NOT_FOUND)










class ProductPagination(PageNumberPagination):
    page_size = 10  # Number of products per page
    page_size_query_param = 'page_size'
    max_page_size = 100

@swagger_auto_schema(
    method='get',
    operation_description="Fetch all products for a specific outlet.",
    responses={
        200: "Products fetched successfully.",
        404: "No products found for this outlet."
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_products(request, outlet_id):
    try:
        # Check if the outlet exists and get the products for the outlet
        products = Product.objects.filter(outlet__id=outlet_id)
        if not products.exists():
            return Response(
                {"error": True, "detail": "No products found for this outlet."},
                status=status.HTTP_404_NOT_FOUND
            )
    except Product.DoesNotExist:
        return Response(
            {"error": True, "detail": "Outlet not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    # Initialize pagination
    paginator = ProductPagination()
    paginated_products = paginator.paginate_queryset(products, request)

    # Serialize the products and variants
    serializer = ProductSerializer(paginated_products, many=True)

    # Construct pagination data with error and detail fields
    response_data = {
        "error": False,
        "detail": "Products fetched successfully.",
        "products": serializer.data,
        "total_products": products.count(),
        "total_pages": paginator.page.paginator.num_pages,
        "current_page": paginator.page.number,
        "products_on_current_page": len(serializer.data),
        "next_page_url": paginator.get_next_link(),
        "previous_page_url": paginator.get_previous_link()
    }

    return Response(response_data, status=status.HTTP_200_OK)










# {
#     "name": "Lunch Menu",
#     "is_enabled": true,
#     "start_date": "2024-11-12",
#     "end_date": "2024-11-30",
#     "open_time": "11:00",
#     "close_time": "15:00",
#     "outlet": 1,
#     "products": [101, 102, 103]
# }
@swagger_auto_schema(
    method='post',
    operation_description="Create a new menu for an outlet.",
    request_body=MenuSerializer,
    responses={
        201: "Menu created successfully.",
        400: "Bad request.",
        401: "Unauthorized.",
        404: "Outlet not found."
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_menu(request,user_id):
    # Authenticate the request
     # Manually handle token authentication
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate the token and retrieve the user
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:  # Check if the token belongs to the user ID provided in the URL
            return Response({"error":True,"detail": "Token is not valid. Invalid Authentication Header"}, status=status.HTTP_403_FORBIDDEN)
        
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
    
    
    serializer = MenuSerializer(data=request.data)
    if serializer.is_valid():
        outlet_id = request.data.get('outlet')
        
        # Verify if the provided outlet exists
        try:
            outlet = Outlet.objects.get(id=outlet_id)
        except Outlet.DoesNotExist:
            return Response({"error": True, "detail": "Outlet not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Save the menu with products
        menu = serializer.save()
        
        return Response({
            "error": False,
            "detail": "Menu created successfully.",
            "menu": serializer.data
        }, status=status.HTTP_201_CREATED)
    
    return Response({"error": True, "detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)






@swagger_auto_schema(
    method='put',
    operation_description="Edit an existing menu.",
    request_body=MenuSerializer,
    responses={
        200: "Menu updated successfully.",
        400: "Bad request.",
        401: "Unauthorized.",
        404: "Menu not found."
    }
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def edit_menu(request, user_id, menu_id):
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:
            return Response({"error": True, "detail": "Token is not valid"}, status=status.HTTP_403_FORBIDDEN)
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        menu = Menu.objects.get(id=menu_id)
    except Menu.DoesNotExist:
        return Response({"error": True, "detail": "Menu not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = MenuSerializer(menu, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"error": False, "detail": "Menu updated successfully", "menu": serializer.data}, status=status.HTTP_200_OK)
    return Response({"error": True, "detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)











@swagger_auto_schema(
    method='post',
    operation_description="Duplicate a menu with all its products.",
    responses={
        201: "Menu duplicated successfully.",
        401: "Unauthorized.",
        404: "Menu not found."
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def duplicate_menu(request, user_id, menu_id):
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:
            return Response({"error": True, "detail": "Token is not valid"}, status=status.HTTP_403_FORBIDDEN)
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        menu = Menu.objects.get(id=menu_id)
    except Menu.DoesNotExist:
        return Response({"error": True, "detail": "Menu not found"}, status=status.HTTP_404_NOT_FOUND)

    new_menu = Menu.objects.create(
        outlet=menu.outlet,
        name=f"{menu.name} (Copy)",
        is_enabled=menu.is_enabled,
        start_date=menu.start_date,
        end_date=menu.end_date,
        open_time=menu.open_time,
        close_time=menu.close_time
    )
    new_menu.products.set(menu.products.all())

    return Response({
        "error": False,
        "detail": "Menu duplicated successfully.",
        "menu_id": new_menu.id,
        "name": new_menu.name
    }, status=status.HTTP_201_CREATED)








@swagger_auto_schema(
    method='patch',
    operation_description="Enable or disable a menu.",
    manual_parameters=[
        openapi.Parameter("is_enabled", openapi.IN_QUERY, description="true or false", type=openapi.TYPE_BOOLEAN)
    ],
    responses={
        200: "Menu status updated successfully.",
        401: "Unauthorized.",
        404: "Menu not found."
    }
)
@api_view(['PATCH'])
@permission_classes([AllowAny])
def toggle_menu(request, user_id, menu_id):
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:
            return Response({"error": True, "detail": "Token is not valid"}, status=status.HTTP_403_FORBIDDEN)
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        menu = Menu.objects.get(id=menu_id)
    except Menu.DoesNotExist:
        return Response({"error": True, "detail": "Menu not found"}, status=status.HTTP_404_NOT_FOUND)

    is_enabled = request.data.get("is_enabled")
    if is_enabled is None:
        return Response({"error": True, "detail": "is_enabled is required"}, status=status.HTTP_400_BAD_REQUEST)

    menu.is_enabled = is_enabled
    menu.save()
    return Response({"error": False, "detail": f"Menu {'enabled' if is_enabled else 'disabled'} successfully."}, status=status.HTTP_200_OK)










@swagger_auto_schema(
    method='post',
    operation_description="Add products to an existing menu.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "products": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER))
        },
        required=["products"]
    ),
    responses={
        200: "Products added successfully.",
        401: "Unauthorized.",
        404: "Menu not found."
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_products_to_menu(request, user_id, menu_id):
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:
            return Response({"error": True, "detail": "Token is not valid"}, status=status.HTTP_403_FORBIDDEN)
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        menu = Menu.objects.get(id=menu_id)
    except Menu.DoesNotExist:
        return Response({"error": True, "detail": "Menu not found"}, status=status.HTTP_404_NOT_FOUND)

    product_ids = request.data.get("products", [])
    if not product_ids:
        return Response({"error": True, "detail": "Products are required"}, status=status.HTTP_400_BAD_REQUEST)

    products = Product.objects.filter(id__in=product_ids)
    menu.products.add(*products)

    return Response({"error": False, "detail": "Products added successfully."}, status=status.HTTP_200_OK)









@swagger_auto_schema(
    method='post',
    operation_description="Remove products from an existing menu.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "products": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER))
        },
        required=["products"]
    ),
    responses={
        200: "Products removed successfully.",
        401: "Unauthorized.",
        404: "Menu not found."
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def remove_products_from_menu(request, user_id, menu_id):
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:
            return Response({"error": True, "detail": "Token is not valid"}, status=status.HTTP_403_FORBIDDEN)
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        menu = Menu.objects.get(id=menu_id)
    except Menu.DoesNotExist:
        return Response({"error": True, "detail": "Menu not found"}, status=status.HTTP_404_NOT_FOUND)

    product_ids = request.data.get("products", [])
    if not product_ids:
        return Response({"error": True, "detail": "Products are required"}, status=status.HTTP_400_BAD_REQUEST)

    products = Product.objects.filter(id__in=product_ids)
    menu.products.remove(*products)

    return Response({"error": False, "detail": "Products removed successfully."}, status=status.HTTP_200_OK)










@swagger_auto_schema(
    method='get',
    operation_description="Get all products of a menu.",
    responses={
        200: "Products fetched successfully.",
        401: "Unauthorized.",
        404: "Menu not found."
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_menu_products(request, user_id, menu_id):
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:
            return Response({"error": True, "detail": "Token is not valid"}, status=status.HTTP_403_FORBIDDEN)
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        menu = Menu.objects.get(id=menu_id)
    except Menu.DoesNotExist:
        return Response({"error": True, "detail": "Menu not found"}, status=status.HTTP_404_NOT_FOUND)

    products = menu.products.all()
    serializer = ProductSerializer(products, many=True)

    return Response({"error": False, "products": serializer.data}, status=status.HTTP_200_OK)
















@swagger_auto_schema(
    method='get',
    operation_description="Fetch menus for a specific outlet.",
    responses={
        200: "Menus fetched successfully.",
        404: "Outlet not found."
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_outlet_menus(request, outlet_id,user_id):
    # Authenticate the request
     # Manually handle token authentication
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate the token and retrieve the user
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:  # Check if the token belongs to the user ID provided in the URL
            return Response({"error":True,"detail": "Token is not valid. Invalid Authentication Header"}, status=status.HTTP_403_FORBIDDEN)
        
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
    
    
    try:
        # Check if the outlet exists
        outlet = Outlet.objects.get(id=outlet_id)
    except Outlet.DoesNotExist:
        return Response({"error": True, "detail": "Outlet not found."}, status=status.HTTP_404_NOT_FOUND)
    
    # Filter menus by outlet
    menus = Menu.objects.filter(outlet=outlet)
    
    # Paginate the response
    paginator = PageNumberPagination()
    paginator.page_size = 10  # Adjust page size as needed
    paginated_menus = paginator.paginate_queryset(menus, request)
    
    # Serialize the paginated menus
    serializer = MenuListSerializer(paginated_menus, many=True)
    
    # Prepare the response
    return paginator.get_paginated_response({
        "error": False,
        "detail": "Menus fetched successfully.",
        "menus": serializer.data
    })











@swagger_auto_schema(
    method='get',
    operation_description="Fetch details of a specific menu.",
    responses={
        200: "Menu details fetched successfully.",
        404: "Menu not found."
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_menu_details(request, menu_id):
    try:
        # Check if the menu exists
        menu = Menu.objects.get(id=menu_id)
    except Menu.DoesNotExist:
        return Response({"error": True, "detail": "Menu not found."}, status=status.HTTP_404_NOT_FOUND)
    
    # Serialize the menu details with products and variants
    serializer = MenuDetailSerializer(menu)
    
    return Response({
        "error": False,
        "detail": "Menu details fetched successfully.",
        "menu": serializer.data
    }, status=status.HTTP_200_OK)












@swagger_auto_schema(
    method='post',
    operation_description="Add a category for a specific outlet.",
    request_body=CategorySerializer,
    responses={
        201: "Category added successfully.",
        400: "Bad request.",
        401: "Unauthorized.",
        404: "Outlet not found."
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_category(request, outlet_id,user_id):
    # Authenticate the request
     # Manually handle token authentication
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate the token and retrieve the user
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:  # Check if the token belongs to the user ID provided in the URL
            return Response({"error":True,"detail": "Token is not valid. Invalid Authentication Header"}, status=status.HTTP_403_FORBIDDEN)
        
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)    
    
    try:
        # Check if the outlet exists
        outlet = Outlet.objects.get(id=outlet_id)

        # Add outlet_id to the request data before passing it to the serializer
        request.data['outlet'] = outlet.id

        # Serialize the category data
        serializer = CategorySerializer(data=request.data)
        
        if serializer.is_valid():
            # Save the category
            category = serializer.save()

            return Response({
                "error": False,
                "detail": "Category created successfully.",
                "category_id": category.id,
                "category_name": category.name,
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "error": True,
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    except Outlet.DoesNotExist:
        return Response({
            "error": True,
            "detail": "Outlet not found."
        }, status=status.HTTP_404_NOT_FOUND)











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
        401: "Unauthorized. Missing or invalid token.",
        403: "Forbidden. Invalid token.",
        404: "Outlet not found."
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_categories_by_outlet(request, outlet_id, user_id):
    # Authenticate the request
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate the token and retrieve the user
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:  # Ensure the token belongs to the provided user ID
            return Response({"error": True, "detail": "Token is not valid. Invalid Authentication Header"}, status=status.HTTP_403_FORBIDDEN)
        
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        # Check if the outlet exists
        outlet = Outlet.objects.get(id=outlet_id)

        # Get categories with both id and name
        categories = Category.objects.filter(outlet=outlet).values("id", "name")

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










@swagger_auto_schema(
    method='put',
    operation_description="Update an employee profile. Only accessible by managers.",
    request_body=EmployeeSerializer,
    responses={
        200: openapi.Response(
            description="Profile updated successfully.",
            examples={
                "application/json": {
                    "error": False,
                    "detail": "Profile updated successfully.",
                    "employee": {
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john.doe@example.com",
                        "phone_number": "1234567890",
                        # Other fields
                    }
                }
            }
        ),
        400: "Bad request. Invalid data.",
        401: "Unauthorized. Missing or invalid token.",
        403: "Forbidden. Only managers can update profiles.",
        404: "Employee not found."
    }
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_profile(request, employee_id,user_id):
    # Manually handle token authentication
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate the token and retrieve the user
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:  # Check if the token belongs to the user ID provided in the URL
            return Response({"error":True,"detail": "Token is not valid. Invalid Authentication Header"}, status=status.HTTP_403_FORBIDDEN)
        
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

   
    # Verify if the requesting user has the "manager" role
    try:
        employee_record = Employee.objects.get(user=requesting_user)
        if employee_record.role != 'manager':
            return Response({"error":True, "detail":"Only a manager can create outlets"}, status=status.HTTP_403_FORBIDDEN)
    except Employee.DoesNotExist:
        return Response({"error":True, "detail": "User is not an employee or manager"}, status=status.HTTP_403_FORBIDDEN)    
    
    try:
        # Retrieve the employee object
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return JsonResponse({"error": True, "detail": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if the authenticated user is the same as the employee's user
    if request.user != employee.user:
        return JsonResponse({"error": True, "detail": "You are not authorized to update this profile."}, status=status.HTTP_403_FORBIDDEN)
    
    # Validate the data (excluding the 'company' and 'user' fields)
    data = request.data.copy()
    
    # Remove company and user from the data to prevent them from being updated
    data.pop('company', None)
    data.pop('user', None)
    
    # Serialize the data and update the employee
    serializer = EmployeeSerializer(employee, data=data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return JsonResponse({
            "error": False,
            "detail": "Profile updated successfully.",
            "employee": serializer.data
        })
    
    return JsonResponse({
        "error": True,
        "detail": "Invalid data.",
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)  










@swagger_auto_schema(
    method='get',
    responses={
        200: StockRequestListSerializer(many=True),
        400: 'Invalid request',
    }
)
@api_view(['GET'])
def get_pending_stock_requests(request, outlet_id,user_id):
    # Manually handle token authentication
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate the token and retrieve the user
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:  # Check if the token belongs to the user ID provided in the URL
            return Response({"error":True,"detail": "Token is not valid. Invalid Authentication Header"}, status=status.HTTP_403_FORBIDDEN)
        
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)    
    
    try:
        # Fetch all pending stock requests for the given outlet
        stock_requests = StockRequest.objects.filter(outlet_id=outlet_id, status='PENDING')

        # Paginate the results
        paginator = PageNumberPagination()
        paginator.page_size = 10  # Customize the number of items per page
        paginated_stock_requests = paginator.paginate_queryset(stock_requests, request)

        # Serialize the data
        serializer = StockRequestListSerializer(paginated_stock_requests, many=True)
        
        # Return paginated response
        return paginator.get_paginated_response(serializer.data)
    
    except Exception as e:
        return Response({
            "error": True,
            "details": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)














@swagger_auto_schema(
    method='patch',
    request_body=ApproveStockRequestSerializer(many=True),
    responses={
        200: 'Stock requests approved successfully',
        400: 'Invalid data provided',
        404: 'Stock request(s) not found',
    }
)
@api_view(['PATCH'])
def approve_stock_requests(request, outlet_id,user_id):
    # Manually handle token authentication
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate the token and retrieve the user
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:  # Check if the token belongs to the user ID provided in the URL
            return Response({"error":True,"detail": "Token is not valid. Invalid Authentication Header"}, status=status.HTTP_403_FORBIDDEN)
        
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        # If a list of stock request IDs is provided
        if isinstance(request.data, list):
            stock_request_ids = [item['id'] for item in request.data]
            stock_requests = StockRequest.objects.filter(id__in=stock_request_ids, outlet_id=outlet_id, status='PENDING')

            # If no matching stock requests are found
            if not stock_requests.exists():
                return Response({
                    "error": True,
                    "details": "No pending stock requests found for the provided IDs."
                }, status=status.HTTP_404_NOT_FOUND)

            # Approve all the stock requests
            for stock_request in stock_requests:
                stock_request.status = 'APPROVED'
                stock_request.save()

            return Response({
                "error": False,
                "details": f"{len(stock_requests)} stock request(s) approved successfully."
            }, status=status.HTTP_200_OK)

        # If a single stock request ID is provided
        elif isinstance(request.data, dict) and 'id' in request.data:
            stock_request = StockRequest.objects.filter(id=request.data['id'], outlet_id=outlet_id, status='PENDING').first()

            if not stock_request:
                return Response({
                    "error": True,
                    "details": "Stock request not found or already processed."
                }, status=status.HTTP_404_NOT_FOUND)

            # Approve the stock request
            stock_request.status = 'APPROVED'
            stock_request.save()

            return Response({
                "error": False,
                "details": f"Stock request {stock_request.id} approved successfully."
            }, status=status.HTTP_200_OK)

        else:
            return Response({
                "error": True,
                "details": "Invalid request format. Please provide either a single or a list of stock request IDs."
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            "error": True,
            "details": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)












@api_view(["POST"])
@permission_classes([AllowAny])
def create_fcm_token(request, outlet_id):
    try:
        # Get outlet by ID
        outlet = get_object_or_404(Outlet, id=outlet_id)

        # Extract token from request data
        token = request.data.get("token")

        if not token:
            return Response(
                {"error": True, "detail": "Token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if token already exists for this outlet
        existing_token = FCMToken.objects.filter(outlet=outlet).first()

        if existing_token:
            existing_token.token = token
            existing_token.save()
            return Response(
                {"error": False, "detail": "FCM Token updated successfully"},
                status=status.HTTP_200_OK,
            )
        else:
            FCMToken.objects.create(outlet=outlet, token=token)
            return Response(
                {"error": False, "detail": "FCM Token created successfully"},
                status=status.HTTP_201_CREATED,
            )

    except Exception as e:
        return Response(
            {"error": True, "detail": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )






@swagger_auto_schema(
    method='get',
    operation_summary="Get all employees for a user's company",
    manual_parameters=[
        openapi.Parameter('Authorization', openapi.IN_HEADER, description="Token", type=openapi.TYPE_STRING),
    ],
    responses={
        200: openapi.Response(description="Success", schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'error': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'detail': openapi.Schema(type=openapi.TYPE_STRING),
                'employees': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
            }
        )),
        401: "Unauthorized",
        403: "Forbidden"
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_employees_by_user(request, user_id):
    # Check for Authorization token
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate token
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:
            return Response({"error": True, "detail": "Token does not belong to this user"}, status=status.HTTP_403_FORBIDDEN)
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    # Get requesting user's employee record and company
    try:
        employee = Employee.objects.get(user=requesting_user)
        base_company = employee.company
    except Employee.DoesNotExist:
        return Response({"error": True, "detail": "User is not associated with any employee record"}, status=status.HTTP_403_FORBIDDEN)

    # Optional filters
    phone = request.query_params.get('phone')
    name = request.query_params.get('name')
    company_id = request.query_params.get('company_id')

    # Start with employees of the base company
    employees = Employee.objects.filter(company=base_company)

    # Apply additional filters
    if phone:
        employees = employees.filter(phone_number__icontains=phone)
    if name:
        employees = employees.filter(
            Q(first_name__icontains=name) |
            Q(last_name__icontains=name)
        )
    if company_id:
        employees = employees.filter(company__id=company_id)

    # Serialize and return
    serializer = EmployeeListSerializer(employees, many=True)
    return Response({
        "error": False,
        "detail": "Employees fetched successfully",
        "employees": serializer.data
    }, status=status.HTTP_200_OK)








@swagger_auto_schema(
    method='post',
    operation_summary="Toggle employee active/inactive status",
    operation_description="Toggle the active status of an employee by ID. Only managers of the same company can perform this action.",
    manual_parameters=[
        openapi.Parameter(
            'Authorization',
            openapi.IN_HEADER,
            description="Authorization token (without 'Token' prefix)",
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="Success response when employee status is toggled",
            examples={
                "application/json": {
                    "error": False,
                    "detail": "Employee has been activated successfully.",
                    "employee_id": 12,
                    "is_active": True
                }
            }
        ),
        401: openapi.Response(description="Unauthorized - Invalid or missing token"),
        403: openapi.Response(description="Forbidden - Not allowed to perform this action"),
        404: openapi.Response(description="Not found - Employee not found in your company")
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def toggle_employee_status(request, employee_id):
    # Authorization check
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        token = Token.objects.get(key=token_key)
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    # Check if requesting user is an employee
    try:
        employee_user = Employee.objects.get(user=requesting_user)
    except Employee.DoesNotExist:
        return Response({"error": True, "detail": "Requesting user is not associated with an employee record"}, status=status.HTTP_403_FORBIDDEN)

    # Only allow manager role to toggle status
    if employee_user.role != 'manager':
        return Response({"error": True, "detail": "Only manager can toggle employee status"}, status=status.HTTP_403_FORBIDDEN)

    # Toggle target employee
    try:
        employee = Employee.objects.get(id=employee_id, company=employee_user.company)
        employee.is_active = not employee.is_active
        employee.save()
        status_str = "activated" if employee.is_active else "deactivated"
        return Response({
            "error": False,
            "detail": f"Employee has been {status_str} successfully.",
            "employee_id": employee.id,
            "is_active": employee.is_active
        }, status=status.HTTP_200_OK)

    except Employee.DoesNotExist:
        return Response({"error": True, "detail": "Employee not found in your company"}, status=status.HTTP_404_NOT_FOUND)










@swagger_auto_schema(
    method='patch',
    operation_summary="Update an employee's permissions",
    manual_parameters=[
        openapi.Parameter('Authorization', openapi.IN_HEADER, description="Token", type=openapi.TYPE_STRING),
    ],
    request_body=EmployeePermissionsUpdateSerializer,
    responses={
        200: openapi.Response(description="Permissions updated", schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "error": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "detail": openapi.Schema(type=openapi.TYPE_STRING),
                "permissions": openapi.Schema(type=openapi.TYPE_OBJECT),
            }
        )),
        400: "Bad Request",
        403: "Forbidden",
        404: "Employee not found"
    }
)
@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_employee_permissions(request,user_id, employee_id):
    # Check for Authorization token
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate token
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:
            return Response({"error": True, "detail": "Token does not belong to this user"}, status=status.HTTP_403_FORBIDDEN)
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    # Get the employee to update
    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

    # Deserialize and validate permissions data
    serializer = EmployeePermissionsUpdateSerializer(data=request.data)
    if serializer.is_valid():
        new_permissions = serializer.validated_data['permissions']

        # Merge existing permissions with new ones (update or add)
        current_permissions = employee.permissions or {}
        current_permissions.update(new_permissions)
        employee.permissions = current_permissions
        employee.save()

        return Response({
            "error": False,
            "detail": "Permissions updated successfully",
            "permissions": employee.permissions
        }, status=status.HTTP_200_OK)

    return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)








@swagger_auto_schema(
    method='get',
    operation_summary="Get credentials for an employee",
    manual_parameters=[
        openapi.Parameter('Authorization', openapi.IN_HEADER, description="Token", type=openapi.TYPE_STRING),
    ],
    responses={
        200: openapi.Response(description="Success", schema=EmployeeCredentialsSerializer),
        401: "Unauthorized",
        403: "Forbidden",
        404: "Credentials not found"
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_employee_credentials(request, employee_id,user_id):
    # Check for Authorization token
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate token
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:
            return Response({"error": True, "detail": "Token does not belong to this user"}, status=status.HTTP_403_FORBIDDEN)
        # requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
    
    # get credentials process
    try:
        credentials = EmployeeCredentials.objects.get(employee_id=employee_id)
    except EmployeeCredentials.DoesNotExist:
        return Response({"error": "Credentials not found for this employee"}, status=status.HTTP_404_NOT_FOUND)

    serializer = EmployeeCredentialsSerializer(credentials)
    return Response({
        "error": False,
        "credentials": serializer.data
    }, status=status.HTTP_200_OK)














@swagger_auto_schema(
    method='post',
    operation_summary="Create or update employee credentials",
    manual_parameters=[
        openapi.Parameter('Authorization', openapi.IN_HEADER, description="Token", type=openapi.TYPE_STRING),
    ],
    request_body=ManageEmployeeCredentialsSerializer,
    responses={
        201: openapi.Response(description="Credentials created"),
        200: openapi.Response(description="Credentials updated"),
        400: "Invalid input",
        401: "Unauthorized",
        403: "Forbidden"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def manage_employee_credentials(request, employee_id,user_id):
     # Check for Authorization token
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    # Validate token
    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:
            return Response({"error": True, "detail": "Token does not belong to this user"}, status=status.HTTP_403_FORBIDDEN)
        # requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
    
    # credentils logic starts here
    try:
        employee = Employee.objects.get(id=employee_id)
        user = employee.user
    except Employee.DoesNotExist:
        return Response({"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = ManageEmployeeCredentialsSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data
    new_email = validated_data['email']
    new_password = validated_data['password']

    # Create or update the credentials
    credentials, created = EmployeeCredentials.objects.get_or_create(employee=employee)

    credentials.email = new_email
    credentials.password = new_password
    credentials.save()

    # Also update in CustomUser
    user.email = new_email
    user.set_password(new_password)
    user.save()

    return Response({
        "error": False,
        "message": "Credentials created successfully." if created else "Credentials updated successfully."
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)










@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'company_id',
            openapi.IN_PATH,
            description="ID of the company",
            type=openapi.TYPE_INTEGER,
            required=True
        ),
        openapi.Parameter(
            'order_number',
            openapi.IN_QUERY,
            description='Search by order number (partial match)',
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'outlet_name',
            openapi.IN_QUERY,
            description='Search by outlet name (partial match)',
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'order_date',
            openapi.IN_QUERY,
            description='Filter by exact order date (format: YYYY-MM-DD)',
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'start_date',
            openapi.IN_QUERY,
            description='Filter by start date for order date range (format: YYYY-MM-DD)',
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'end_date',
            openapi.IN_QUERY,
            description='Filter by end date for order date range (format: YYYY-MM-DD)',
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'page',
            openapi.IN_QUERY,
            description='Page number for pagination',
            type=openapi.TYPE_INTEGER,
            required=False
        ),
    ],
    responses={
        200: openapi.Response(
            description="List of company orders with pagination and filters",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'total_orders': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'current_page': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'next_page_url': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, nullable=True),
                    'previous_page_url': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, nullable=True),
                    'orders': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                }
            )
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_company_orders(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    orders = Order.objects.filter(outlet__company=company).order_by('-order_date')

    # 🔍 Filter by order number
    order_number = request.query_params.get('order_number')
    if order_number:
        orders = orders.filter(order_number__icontains=order_number)

    # 🔍 Filter by outlet name
    outlet_name = request.query_params.get('outlet_name')
    if outlet_name:
        orders = orders.filter(outlet__outlet_name__icontains=outlet_name)

    # 🔍 Filter by specific order_date (YYYY-MM-DD)
    order_date = request.query_params.get('order_date')
    if order_date:
        try:
            date_obj = datetime.strptime(order_date, "%Y-%m-%d").date()
            orders = orders.filter(order_date__date=date_obj)
        except ValueError:
            return Response({'detail': 'Invalid order_date format. Use YYYY-MM-DD.'}, status=400)

    # 🔍 Filter by date range (start_date and end_date)
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    if start_date and end_date:
        try:
            start_obj = datetime.strptime(start_date, "%Y-%m-%d")
            end_obj = datetime.strptime(end_date, "%Y-%m-%d")
            orders = orders.filter(order_date__date__range=(start_obj.date(), end_obj.date()))
        except ValueError:
            return Response({'detail': 'Invalid start_date or end_date format. Use YYYY-MM-DD.'}, status=400)

    paginator = PageNumberPagination()
    paginator.page_size = 10
    paginated_orders = paginator.paginate_queryset(orders, request)

    serializer = OrderSerializer(paginated_orders, many=True)

    return Response({
        "total_orders": orders.count(),
        "current_page": paginator.page.number,
        "total_pages": paginator.page.paginator.num_pages,
        "next_page_url": paginator.get_next_link(),
        "previous_page_url": paginator.get_previous_link(),
        "orders": serializer.data,
    })







@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'order_number',
            openapi.IN_PATH,
            description="Order number (e.g. ABC1234567)",
            type=openapi.TYPE_STRING
        )
    ],
    responses={200: OrderDetailSerializer()}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_order_details_by_number(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    serializer = OrderDetailSerializer(order)
    return Response(serializer.data)








@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('order_number', openapi.IN_PATH, description="Unique order number", type=openapi.TYPE_STRING),
    ],
    responses={200: 'HTML bill rendered'}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def generate_order_bill(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    outlet = order.outlet
    customer = order.customers.first()  # assuming one customer per order

    items_data = []
    subtotal = 0

    for item in order.items.all():
        product_name = item.product.name if item.product else None
        variant_name = item.product_variant.name if item.product_variant else None

        items_data.append({
            'product_name': product_name,
            'variant_name': variant_name,
            'quantity': item.quantity,
            'price': item.price,
            'total_price': item.total_price
        })

        subtotal += item.total_price or 0

    cgst = sgst = float(order.gst) / 2 if order.gst else 0
    formatted_date = localtime(order.order_date).strftime('%d-%m-%Y %I:%M %p')

    context = {
        "outlet": {
            "logo": outlet.logo.url if outlet.logo else '',
            "outlet_name": outlet.outlet_name,
            "address": outlet.address,
            "phone_number": outlet.phone_number
        },
        "customer": {
            "name": customer.name if customer else '',
            "phone_number": customer.phone_number if customer else ''
        },
        "order_number": order.order_number,
        "formatted_date": formatted_date,
        "items": items_data,
        "subtotal": subtotal,
        "cgst": f"{cgst:.2f}",
        "sgst": f"{sgst:.2f}",
        "total_price": order.total_price,
        "mode": order.mode
    }

    html_content = render_to_string("bill.html", context)
    return HttpResponse(html_content)







# {
#     "refund_title": "Order Delay Compensation",
#     "refund_description": "Customer received order late. 20% refund issued.",
#     "refund_amount": 50.00
# }



@swagger_auto_schema(
    method='post',
    request_body=RefundNoteSerializer,
    responses={
        201: openapi.Response('Refund note created successfully', RefundNoteSerializer),
        400: 'Bad Request',
        404: 'Order not found'
    },
    operation_description="Add a refund note to an order using the order number and mark order as REFUNDED."
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_refund_note(request, order_number):
    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return Response({'detail': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = RefundNoteSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(order=order)

        # ✅ Change order status to 'REFUNDED'
        order.status = 'REFUNDED'
        order.save(update_fields=['status'])

        return Response({
            'detail': 'Refund note added successfully and order status updated to REFUNDED',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response('List of refund notes for the given order', RefundNoteSerializer(many=True)),
        404: 'Order not found'
    },
    operation_description="Retrieve all refund notes for a given order by order number."
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_refund_notes_by_order(request, order_number):
    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return Response({'detail': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    refund_notes = RefundNote.objects.filter(order=order)
    serializer = RefundNoteSerializer(refund_notes, many=True)
    return Response({'order_number': order_number, 'refund_notes': serializer.data}, status=status.HTTP_200_OK)








@swagger_auto_schema(
    method='post',
    responses={
        200: openapi.Response(description="Order cancelled successfully"),
        404: "Order not found"
    },
    operation_description="Cancel an order using its order number. Updates the status to CANCELLED."
)
@api_view(['POST'])
@permission_classes([AllowAny])
def cancel_order(request, order_number):
    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return Response({'detail': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    order.status = 'CANCELLED'
    order.save(update_fields=['status'])

    return Response({'error':False,'detail': f'Order {order_number} cancelled successfully'}, status=status.HTTP_200_OK)








class FlatPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'

    def get_page_metadata(self):
        total_customers = self.page.paginator.count
        total_pages = math.ceil(total_customers / self.page_size)
        current_page = self.page.number
        next_page = self.get_next_link()
        previous_page = self.get_previous_link()
        return {
            "total_customers": total_customers,
            "total_pages": total_pages,
            "current_page": current_page,
            "next_page_url": next_page,
            "previous_page_url": previous_page,
        }




@swagger_auto_schema(
    method='get',
    operation_description="Get list of customers for a company with last order info and outlet details. Also returns outlet stats.",
    manual_parameters=[
        openapi.Parameter(
            'company_id',
            openapi.IN_PATH,
            description="ID of the company",
            type=openapi.TYPE_INTEGER,
            required=True
        ),
        openapi.Parameter(
            'outlet_id',
            openapi.IN_QUERY,
            description="Optional outlet ID to filter customers",
            type=openapi.TYPE_INTEGER,
            required=False
        ),
    ],
    responses={
        200: openapi.Response(
            description="List of customers and outlet statistics",
            examples={
                "application/json": {
                    "error": False,
                    "customers": [
                        {
                            "name": "John Doe",
                            "phone_number": "9876543210",
                            "last_order_date": "2025-06-15T14:30:00Z",
                            "outlet": {
                                "id": 5,
                                "name": "Outlet A"
                            }
                        }
                    ],
                    "outlet_summary": {
                        "total_outlets": 8,
                        "active_outlets": 6,
                        "new_outlets_this_month": 2
                    }
                }
            }
        ),
        404: "Company not found",
        400: "Bad request"
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_company_customers(request, company_id):
    outlet_id = request.query_params.get('outlet_id')
    search_query = request.query_params.get('phone_number', '')
    today = now()

    # Validate company
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return Response({"error": True, "detail": "Company not found."}, status=status.HTTP_404_NOT_FOUND)

    # Get relevant outlets
    all_outlets = Outlet.objects.filter(company=company)
    if outlet_id:
        all_outlets = all_outlets.filter(id=outlet_id)
    outlet_ids = all_outlets.values_list('id', flat=True)

    # Get orders and customers
    orders = Order.objects.filter(outlet_id__in=outlet_ids)
    customers = Customer.objects.filter(order__in=orders).distinct()

    # Apply phone search if present
    if search_query:
        customers = customers.filter(phone_number__icontains=search_query)

    # Stats
    total_customers = customers.count()
    active_customers = customers.filter(
        order__order_date__year=today.year,
        order__order_date__month=today.month
    ).distinct().count()

    # New customers this month
    first_orders = customers.annotate(first_order=Min('order__order_date'))
    new_customers_this_month = sum(
        1 for c in first_orders if c.first_order and c.first_order.year == today.year and c.first_order.month == today.month
    )

    # Prepare customer data
    customer_data = []
    for customer in customers:
        latest_order = orders.filter(customers=customer).order_by('-order_date').first()
        if latest_order:
            customer_data.append({
                "name": customer.name,
                "phone_number": customer.phone_number,
                "last_order_date": latest_order.order_date,
                "outlet": {
                    "id": latest_order.outlet.id,
                    "name": latest_order.outlet.outlet_name
                }
            })

    # Paginate
    paginator = FlatPagination()
    paginated_data = paginator.paginate_queryset(customer_data, request)
    page_metadata = paginator.get_page_metadata()

    # Final response
    return Response({
        "total_customers": total_customers,
        "active_customers": active_customers,
        "new_customers_this_month": new_customers_this_month,
        "total_pages": page_metadata["total_pages"],
        "current_page": page_metadata["current_page"],
        "next_page_url": page_metadata["next_page_url"],
        "previous_page_url": page_metadata["previous_page_url"],
        "customers": paginated_data
    }, status=status.HTTP_200_OK)










@swagger_auto_schema(
    method='put',
    operation_summary="Edit Category",
    operation_description="Edits an existing category by ID for a specific outlet.",
    request_body=CategorySerializer,
    responses={
        200: openapi.Response("Category updated successfully"),
        400: "Validation error",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Category not found",
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([AllowAny])
def edit_category(request, outlet_id, user_id, category_id):
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:
            return Response({"error": True, "detail": "Token is not valid. Invalid Authentication Header"}, status=status.HTTP_403_FORBIDDEN)

        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        category = Category.objects.get(id=category_id, outlet__id=outlet_id)
    except Category.DoesNotExist:
        return Response({"error": True, "detail": "Category not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = CategorySerializer(category, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "error": False,
            "detail": "Category updated successfully.",
            "category_id": category.id,
            "category_name": category.name
        }, status=status.HTTP_200_OK)
    else:
        return Response({"error": True, "detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)












@swagger_auto_schema(
    method='delete',
    operation_summary="Delete Category",
    operation_description="Deletes an existing category by ID for a specific outlet.",
    responses={
        200: "Category deleted successfully",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Category not found",
    }
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_category(request, outlet_id, user_id, category_id):
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:
            return Response({"error": True, "detail": "Token is not valid. Invalid Authentication Header"}, status=status.HTTP_403_FORBIDDEN)

        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        category = Category.objects.get(id=category_id, outlet__id=outlet_id)
        category.delete()
        return Response({
            "error": False,
            "detail": "Category deleted successfully."
        }, status=status.HTTP_200_OK)
    except Category.DoesNotExist:
        return Response({
            "error": True,
            "detail": "Category not found."
        }, status=status.HTTP_404_NOT_FOUND)











# @api_view(["GET"])
# def dashboard_data(request):
#     outlet_id = request.query_params.get("outlet_id")

#     # Base orders queryset (optionally filtered by outlet)
#     orders_qs = Order.objects.all()
#     if outlet_id:
#         orders_qs = orders_qs.filter(outlet_id=outlet_id)

#     # ---------- SUMMARY CARDS ----------
#     total_orders = orders_qs.count()
#     total_sales = (
#         orders_qs.filter(status__in=["CONFIRMED", "COMPLETED"])
#         .aggregate(total=Sum("total_price"))
#         .get("total") or 0
#     )

#     if outlet_id:
#         total_outlets = 1
#     else:
#         total_outlets = Outlet.objects.count()

#     total_customers = (
#         Customer.objects.filter(order__in=orders_qs)
#         .values("phone_number")
#         .distinct()
#         .count()
#     )

#     summary_cards = [
#         {
#             "key": "total_orders",
#             "label": "Total Orders",
#             "value": total_orders,
#         },
#         {
#             "key": "total_sales",
#             "label": "Total Sales",
#             "value": float(total_sales),
#         },
#         {
#             "key": "total_outlets",
#             "label": "Total Outlets",
#             "value": total_outlets,
#         },
#         {
#             "key": "total_customers",
#             "label": "Total Customers",
#             "value": total_customers,
#         },
#     ]

#     # ---------- LINE CHART: DAILY SALES (LAST 7 DAYS) ----------
#     today = timezone.now().date()
#     start_date = today - timedelta(days=6)

#     sales_raw = (
#         orders_qs.filter(
#             status__in=["CONFIRMED", "COMPLETED"],
#             order_date__date__gte=start_date,
#         )
#         .annotate(day=TruncDate("order_date"))
#         .values("day")
#         .annotate(total=Sum("total_price"))
#         .order_by("day")
#     )

#     sales_dict = {item["day"]: item["total"] or 0 for item in sales_raw}

#     labels = []
#     data = []
#     for i in range(7):
#         day = start_date + timedelta(days=i)
#         labels.append(day.strftime("%Y-%m-%d"))
#         data.append(float(sales_dict.get(day, 0)))

#     sales_line_chart = {
#         "labels": labels,
#         "data": data,
#     }

#     # ---------- LAST 3 HOURS TABLE ----------
#     three_hours_ago = timezone.now() - timedelta(hours=3)
#     recent_orders = (
#         orders_qs.filter(order_date__gte=three_hours_ago)
#         .order_by("-order_date")[:10]
#     )

#     recent_orders_rows = [
#         {
#             "order_number": o.order_number,
#             "status": o.status,
#             "total_amount": float(o.total_price),
#             "mode": o.mode,
#             "order_time": o.order_date.strftime("%H:%M"),
#         }
#         for o in recent_orders
#     ]

#     recent_orders_table = {
#         "title": "Last 3 Hours Orders",
#         "rows": recent_orders_rows,
#     }

#     # ---------- STATUS CARDS (PENDING / CONFIRMED / REFUNDED) ----------
#     status_counts_raw = orders_qs.values("status").annotate(count=Count("id"))
#     base_status = {"PENDING": 0, "CONFIRMED": 0, "REFUNDED": 0}
#     for item in status_counts_raw:
#         if item["status"] in base_status:
#             base_status[item["status"]] = item["count"]

#     order_status_cards = {
#         "pending_orders": base_status["PENDING"],
#         "confirmed_orders": base_status["CONFIRMED"],
#         "refunded_orders": base_status["REFUNDED"],
#     }

#     # ---------- LOW STOCK ITEMS ----------
#     low_stock_products = Product.objects.filter(is_stock_out=True)
#     low_stock_variants = ProductVariant.objects.filter(is_stock_out=True)

#     if outlet_id:
#         low_stock_products = low_stock_products.filter(outlet_id=outlet_id)
#         low_stock_variants = low_stock_variants.filter(
#             product__outlet_id=outlet_id
#         )

#     low_stock_items = []

#     for p in low_stock_products[:5]:
#         low_stock_items.append(
#             {
#                 "name": p.name,
#                 "type": "product",
#                 "outlet": p.outlet.outlet_name,
#             }
#         )

#     remaining_slots = max(0, 5 - len(low_stock_items))
#     if remaining_slots:
#         for v in low_stock_variants[:remaining_slots]:
#             low_stock_items.append(
#                 {
#                     "name": f"{v.product.name} - {v.name}",
#                     "type": "variant",
#                     "outlet": v.product.outlet.outlet_name,
#                 }
#             )

#     # ---------- FINAL RESPONSE ----------
#     payload = {
#         "summary_cards": summary_cards,
#         "sales_line_chart": sales_line_chart,
#         "recent_orders_table": recent_orders_table,
#         "order_status_cards": order_status_cards,
#         "low_stock_items": low_stock_items,
#     }

#     return Response(payload)



@swagger_auto_schema(
    method='get',
    operation_description="Returns dashboard data for the admin panel.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "summary_cards": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "key": openapi.Schema(type=openapi.TYPE_STRING),
                        "label": openapi.Schema(type=openapi.TYPE_STRING),
                        "value": openapi.Schema(type=openapi.TYPE_NUMBER),
                    }
                )),
                "sales_line_chart": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "labels": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        "data": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_NUMBER)),
                    }
                ),
                "recent_orders_table": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "title": openapi.Schema(type=openapi.TYPE_STRING),
                        "rows": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "order_number": openapi.Schema(type=openapi.TYPE_STRING),
                                "status": openapi.Schema(type=openapi.TYPE_STRING),
                                "total_amount": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "mode": openapi.Schema(type=openapi.TYPE_STRING),
                                "order_time": openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        )),
                    }
                ),
                "order_status_cards": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "pending_orders": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "confirmed_orders": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "refunded_orders": openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                ),
                "low_stock_items": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "name": openapi.Schema(type=openapi.TYPE_STRING),
                            "type": openapi.Schema(type=openapi.TYPE_STRING),
                            "outlet": openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    )
                ),
            }
        )
    }
)
@api_view(["GET"])
@permission_classes([AllowAny])
def dashboard_sample_data(request):
    data = {

        # -----------------------------------------
        # 🔵 SUMMARY CARDS (TOP 4 CARDS)
        # -----------------------------------------
        "summary_cards": [
            {
                "key": "total_orders",
                "label": "Total Orders",
                "value": 1280,
            },
            {
                "key": "total_sales",
                "label": "Total Sales",
                "value": 452000.75,
            },
            {
                "key": "total_outlets",
                "label": "Total Outlets",
                "value": 4,
            },
            {
                "key": "total_customers",
                "label": "Total Customers",
                "value": 980,
            },
        ],

        # -----------------------------------------
        # 🔵 LINE CHART — LAST 7 DAYS SALES
        # -----------------------------------------
        "sales_line_chart": {
            "labels": [
                "2025-11-20",
                "2025-11-21",
                "2025-11-22",
                "2025-11-23",
                "2025-11-24",
                "2025-11-25",
                "2025-11-26"
            ],
            "data": [12000, 15000, 18000, 17000, 22000, 25000, 28000]
        },

        # -----------------------------------------
        # 🔵 LAST 3 HOURS ORDERS TABLE
        # -----------------------------------------
        "recent_orders_table": {
            "title": "Last 3 Hours Orders",
            "rows": [
                {
                    "order_number": "ORD123456",
                    "status": "CONFIRMED",
                    "total_amount": 1450.00,
                    "mode": "upi",
                    "order_time": "12:40",
                },
                {
                    "order_number": "ORD123457",
                    "status": "PENDING",
                    "total_amount": 220.00,
                    "mode": "cash",
                    "order_time": "11:55",
                },
                {
                    "order_number": "ORD123458",
                    "status": "COMPLETED",
                    "total_amount": 980.00,
                    "mode": "upi",
                    "order_time": "10:45",
                },
            ]
        },

        # -----------------------------------------
        # 🔵 STATUS OVERVIEW: PENDING, CONFIRMED, REFUNDED
        # -----------------------------------------
        "order_status_cards": {
            "pending_orders": 12,
            "confirmed_orders": 89,
            "refunded_orders": 3
        },

        # -----------------------------------------
        # 🔵 LOW STOCK ITEMS
        # -----------------------------------------
        "low_stock_items": [
            {
                "name": "Cold Coffee",
                "type": "product",
                "outlet": "Outlet A"
            },
            {
                "name": "Veg Burger - Large",
                "type": "variant",
                "outlet": "Outlet A"
            },
            {
                "name": "French Fries",
                "type": "product",
                "outlet": "Outlet B"
            },
            {
                "name": "Cheese Sandwich",
                "type": "product",
                "outlet": "Outlet C"
            },
            {
                "name": "Chicken Roll - Spicy",
                "type": "variant",
                "outlet": "Outlet D"
            },
        ],
    }

    return Response(data)





# ========== 1. SALES REPORT ==========
@swagger_auto_schema(
    method='get',
    operation_description="Sales report with KPIs and daily sales.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "total_sales": openapi.Schema(type=openapi.TYPE_NUMBER),
                "total_orders": openapi.Schema(type=openapi.TYPE_INTEGER),
                "avg_order_value": openapi.Schema(type=openapi.TYPE_NUMBER),
                "kpis": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "label": openapi.Schema(type=openapi.TYPE_STRING),
                            "value": openapi.Schema(type=openapi.TYPE_NUMBER),
                            "unit": openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    )
                ),
                "daily_sales": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "date": openapi.Schema(type=openapi.TYPE_STRING),
                            "total": openapi.Schema(type=openapi.TYPE_NUMBER),
                        }
                    )
                ),
            }
        )
    }
)
@api_view(["GET"])
def sales_report_sample(request, outlet_id):
    data = {
        "total_sales": 452000.75,
        "total_orders": 1280,
        "avg_order_value": 353.13,
        "kpis": [
            {"label": "Today Sales", "value": 28000, "unit": "INR"},
            {"label": "Yesterday Sales", "value": 25000, "unit": "INR"},
            {"label": "Week Sales", "value": 172000, "unit": "INR"},
        ],
        "daily_sales": [
            {"date": "2025-11-20", "total": 12000},
            {"date": "2025-11-21", "total": 15000},
            {"date": "2025-11-22", "total": 18000},
            {"date": "2025-11-23", "total": 17000},
            {"date": "2025-11-24", "total": 22000},
            {"date": "2025-11-25", "total": 25000},
            {"date": "2025-11-26", "total": 28000},
        ],
    }
    return Response(data)


# ========== 2. ORDERS REPORT ==========
@swagger_auto_schema(
    method='get',
    operation_description="Orders report with status breakdown.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "total_orders": openapi.Schema(type=openapi.TYPE_INTEGER),
                "status_breakdown": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    additional_properties=openapi.Schema(type=openapi.TYPE_INTEGER),
                ),
                "kpis": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "label": openapi.Schema(type=openapi.TYPE_STRING),
                            "value": openapi.Schema(type=openapi.TYPE_NUMBER),
                        }
                    )
                ),
                "recent_orders": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "order_number": openapi.Schema(type=openapi.TYPE_STRING),
                            "status": openapi.Schema(type=openapi.TYPE_STRING),
                            "amount": openapi.Schema(type=openapi.TYPE_NUMBER),
                            "mode": openapi.Schema(type=openapi.TYPE_STRING),
                            "order_time": openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    )
                ),
            }
        )
    }
)
@api_view(["GET"])
def orders_report_sample(request, outlet_id):
    data = {
        "total_orders": 1280,
        "status_breakdown": {
            "PENDING": 32,
            "PROCESSING": 45,
            "CONFIRMED": 780,
            "COMPLETED": 380,
            "CANCELLED": 25,
            "REFUNDED": 18,
        },
        "kpis": [
            {"label": "Today Orders", "value": 160},
            {"label": "Avg Orders / Day", "value": 140},
            {"label": "Cancellation Rate %", "value": 1.9},
        ],
        "recent_orders": [
            {
                "order_number": "ORD123460",
                "status": "COMPLETED",
                "amount": 1450.0,
                "mode": "upi",
                "order_time": "12:40",
            },
            {
                "order_number": "ORD123461",
                "status": "PENDING",
                "amount": 220.0,
                "mode": "cash",
                "order_time": "12:15",
            },
            {
                "order_number": "ORD123462",
                "status": "REFUNDED",
                "amount": 520.0,
                "mode": "upi",
                "order_time": "11:50",
            },
        ],
    }
    return Response(data)


# ========== 3. CUSTOMERS REPORT ==========
@swagger_auto_schema(
    method='get',
    operation_description="Customers report with KPIs and top customers.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "total_customers": openapi.Schema(type=openapi.TYPE_INTEGER),
                "new_customers_7d": openapi.Schema(type=openapi.TYPE_INTEGER),
                "repeat_customers_rate": openapi.Schema(type=openapi.TYPE_NUMBER),
                "kpis": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "label": openapi.Schema(type=openapi.TYPE_STRING),
                            "value": openapi.Schema(type=openapi.TYPE_NUMBER),
                            "unit": openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    )
                ),
                "top_customers": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "name": openapi.Schema(type=openapi.TYPE_STRING),
                            "phone": openapi.Schema(type=openapi.TYPE_STRING),
                            "orders_count": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "total_spent": openapi.Schema(type=openapi.TYPE_NUMBER),
                        }
                    )
                ),
            }
        )
    }
)
@api_view(["GET"])
def customers_report_sample(request, outlet_id):
    data = {
        "total_customers": 980,
        "new_customers_7d": 120,
        "repeat_customers_rate": 62.5,  # %
        "kpis": [
            {"label": "Avg Orders / Customer", "value": 3.1, "unit": ""},
            {"label": "CLTV (Approx.)", "value": 1800, "unit": "INR"},
            {"label": "Active Customers (30d)", "value": 640, "unit": ""},
        ],
        "top_customers": [
            {
                "name": "Rahul Sharma",
                "phone": "9876543210",
                "orders_count": 22,
                "total_spent": 15400.0,
            },
            {
                "name": "Priya Verma",
                "phone": "9876500012",
                "orders_count": 18,
                "total_spent": 13120.5,
            },
            {
                "name": "Aman Gupta",
                "phone": "9898989898",
                "orders_count": 15,
                "total_spent": 11050.0,
            },
        ],
    }
    return Response(data)


# ========== 4. OUTLET REPORT ==========
@swagger_auto_schema(
    method='get',
    operation_description="Outlet-wise report with KPIs.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "total_outlets": openapi.Schema(type=openapi.TYPE_INTEGER),
                "kpis": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "label": openapi.Schema(type=openapi.TYPE_STRING),
                            "value": openapi.Schema(type=openapi.TYPE_NUMBER),
                            "unit": openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    )
                ),
                "outlets": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "outlet_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "name": openapi.Schema(type=openapi.TYPE_STRING),
                            "city": openapi.Schema(type=openapi.TYPE_STRING),
                            "total_sales": openapi.Schema(type=openapi.TYPE_NUMBER),
                            "total_orders": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "avg_order_value": openapi.Schema(type=openapi.TYPE_NUMBER),
                            "is_active": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        }
                    )
                ),
            }
        )
    }
)
@api_view(["GET"])
def outlet_report_sample(request, company_id):
    data = {
        "total_outlets": 4,
        "kpis": [
            {"label": "Active Outlets", "value": 4, "unit": ""},
            {"label": "Avg Sales / Outlet (Day)", "value": 42000, "unit": "INR"},
            {"label": "Best Performing Outlet ID", "value": 2, "unit": ""},
        ],
        "outlets": [
            {
                "outlet_id": 1,
                "name": "Outlet A",
                "city": "Mumbai",
                "total_sales": 152000.0,
                "total_orders": 420,
                "avg_order_value": 362.0,
                "is_active": True,
            },
            {
                "outlet_id": 2,
                "name": "Outlet B",
                "city": "Delhi",
                "total_sales": 181500.0,
                "total_orders": 510,
                "avg_order_value": 356.0,
                "is_active": True,
            },
            {
                "outlet_id": 3,
                "name": "Outlet C",
                "city": "Pune",
                "total_sales": 68000.0,
                "total_orders": 210,
                "avg_order_value": 323.0,
                "is_active": True,
            },
            {
                "outlet_id": 4,
                "name": "Outlet D",
                "city": "Bangalore",
                "total_sales": 50500.0,
                "total_orders": 140,
                "avg_order_value": 360.0,
                "is_active": False,
            },
        ],
    }
    return Response(data)








# ----------- SET PRINTER CONFIG ------------
@swagger_auto_schema(
    method='post',
    operation_description="Save printer names for an outlet.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "printers": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING)
            ),
        },
        required=["printers"],
    ),
    responses={200: "Printer configuration saved."}
)
@api_view(["POST"])
def set_printer_config(request, outlet_id):
    try:
        outlet = Outlet.objects.get(id=outlet_id)
    except Outlet.DoesNotExist:
        return Response({"error": "Outlet not found"}, status=404)

    printer_names = request.data.get("printers", [])

    config, created = PrinterConfig.objects.get_or_create(outlet=outlet)
    config.printers = printer_names
    config.save()

    return Response({
        "message": "Printer configuration saved",
        "outlet": outlet.outlet_name,
        "printers": config.printers
    })
    

# ----------- GET PRINTER CONFIG ------------
@swagger_auto_schema(
    method='get',
    operation_description="Get printer names configured for an outlet.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "outlet": openapi.Schema(type=openapi.TYPE_STRING),
                "printers": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING)
                ),
            }
        )
    }
)
@api_view(["GET"])
def get_printer_config(request, outlet_id):
    try:
        outlet = Outlet.objects.get(id=outlet_id)
    except Outlet.DoesNotExist:
        return Response({"error": "Outlet not found"}, status=404)

    config = PrinterConfig.objects.filter(outlet=outlet).first()

    if not config:
        return Response({
            "outlet": outlet.outlet_name,
            "printers": []
        })

    return Response({
        "outlet": outlet.outlet_name,
        "printers": config.printers
    })




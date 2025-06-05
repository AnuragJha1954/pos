import random
import string

from django.shortcuts import get_object_or_404,render
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.utils.timezone import localtime
from django.template.loader import render_to_string
from django.http import HttpResponse

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
    Customer
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
    OrderBillSerializer
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
def list_company_outlets(request, company_id,user_id):
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
            return Response({"error":True, "detail":"Only a manager can get list of all outlets of a company"}, status=status.HTTP_403_FORBIDDEN)
    except Employee.DoesNotExist:
        return Response({"error":True, "detail": "User is not an employee or manager"}, status=status.HTTP_403_FORBIDDEN)
    
    
    outlets = Outlet.objects.filter(company_id=company_id)
    serializer = OutletSerializer(outlets, many=True)
    return Response({"error": False, "outlets": serializer.data})





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
        company = employee.company
    except Employee.DoesNotExist:
        return Response({"error": True, "detail": "User is not associated with any employee record"}, status=status.HTTP_403_FORBIDDEN)

    # Get all employees of the same company
    employees = Employee.objects.filter(company=company)

    # Serialize and return
    serializer = EmployeeListSerializer(employees, many=True)
    return Response({"error": False, "detail":"Employess fetched successfully", "employees": serializer.data}, status=status.HTTP_200_OK)









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
            'page',
            openapi.IN_QUERY,
            description='Page number for pagination',
            type=openapi.TYPE_INTEGER,
            required=False
        )
    ],
    responses={
        200: openapi.Response(
            description="List of company orders with pagination",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'orders': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                    'total_orders': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'current_page': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'next_page_url': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, nullable=True),
                    'previous_page_url': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, nullable=True),
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


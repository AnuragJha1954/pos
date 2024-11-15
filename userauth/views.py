import random

from django.shortcuts import render
from django.core.mail import send_mail
from django.template.loader import render_to_string

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token

from .serializers import ( 
    CompanyUserSerializer,
    EmailSerializer, 
    OTPVerificationSerializer, 
    CustomUserLoginSerializer
)

from .models import OTPDetails
from users.models import CustomUser
from v1.models import (
    Company,
    Plan,
    PlanAssignment, 
    Employee
)


# Create your views here.

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'company_name': openapi.Schema(type=openapi.TYPE_STRING, description='The name of the company'),
            'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='The email of the user'),
            'number_of_outlets': openapi.Schema(type=openapi.TYPE_INTEGER, description='The number of outlets for the company'),
            'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='The phone number of the user'),
            'verified': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Verification status of the user'),
        },
        required=['company_name', 'email', 'number_of_outlets']
    ),
    responses={
        201: openapi.Response(
            description='User created successfully',
            examples={
                'application/json': {
                    'error': False,
                    'detail': 'User created successfully. OTP has been sent to your email.',
                    'username': 'example_username',
                    'user_id': 1,
                    'email': 'example@example.com'
                }
            }
        ),
        400: openapi.Response(
            description='Bad request',
            examples={
                'application/json': {
                    'error': True,
                    'detail': {'field_name': ['error message']}
                }
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_user(request):
    serializer = CompanyUserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # Generate a random 6-digit OTP
        otp = f"{random.randint(100000, 999999)}"

        # Save OTP details in the database
        OTPDetails.objects.update_or_create(email=user.email, defaults={'otp': otp})
        
        # Render email content from the HTML template
        html_message = render_to_string('otp.html', {'otp': otp})
        
        # Send the OTP to the email
        send_mail(
            subject="Your OTP Code",
            message="",  # Leave the plain message empty
            from_email=None,  # Use default email settings or configure as needed
            recipient_list=[user.email],
            html_message=html_message  # Only HTML version is provided
        )

        return Response({
            "error": False,
            "detail": "User created successfully. OTP has been sent to your email.",
            "username": user.username,
            "user_id": user.id,
            "email": user.email
        }, status=status.HTTP_201_CREATED)
    
    return Response({"error": True, "detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)




@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            'user_id',
            openapi.IN_PATH,
            description='ID of the user for whom the OTP needs to be resent',
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description='OTP has been resent successfully',
            examples={
                'application/json': {
                    'error': False,
                    'detail': 'OTP has been resent to your email.'
                }
            }
        ),
        404: openapi.Response(
            description='User or OTP record not found',
            examples={
                'application/json': {
                    'error': True,
                    'detail': 'User not found.'  # or 'No OTP record found for this email.'
                }
            }
        ),
        400: openapi.Response(
            description='Bad request',
            examples={
                'application/json': {
                    'error': True,
                    'detail': 'Invalid request.'
                }
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request, user_id):
    try:
        # Retrieve the user by user_id
        user = CustomUser.objects.get(id=user_id)
        email = user.email
        
        # Generate a random 6-digit OTP
        otp = f"{random.randint(100000, 999999)}"
        
        # Save OTP details in the database
        OTPDetails.objects.update_or_create(email=user.email, defaults={'otp': otp})
        
        # # Send the OTP to the email
        # send_mail(
        #     subject="Your OTP Code",
        #     message=f"Your OTP code is {otp}.",
        #     from_email=None,  # Use default email settings or configure as needed
        #     recipient_list=[email],
        # )
        
                # Render email content from the HTML template
        html_message = render_to_string('otp.html', {'otp': otp})
        
        # Send the OTP to the email
        send_mail(
            subject="Your OTP Code",
            message="",  # Leave the plain message empty
            from_email=None,  # Use default email settings or configure as needed
            recipient_list=[user.email],
            html_message=html_message  # Only HTML version is provided
        )
        
        return Response({"error": False, "detail": "OTP has been resent to your email."}, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({"error": True, "detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)







@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'otp': openapi.Schema(type=openapi.TYPE_STRING, description='The OTP sent to the user'),
        },
        required=['otp']
    ),
    responses={
        200: openapi.Response(
            description='OTP verified successfully',
            examples={
                'application/json': {
                    'error': False,
                    'detail': 'OTP verified successfully. Username and password have been sent to your email.'
                }
            }
        ),
        400: openapi.Response(
            description='Bad request',
            examples={
                'application/json': {
                    'error': True,
                    'detail': 'Invalid OTP.'  # or 'No OTP record found for this email.' or other relevant messages
                }
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request, user_id):
    serializer = OTPVerificationSerializer(data=request.data)
    if serializer.is_valid():
        otp = serializer.validated_data['otp']
        
        try:
            # Retrieve the user by user_id
            user = CustomUser.objects.get(id=user_id)
            email = user.email

            # Retrieve OTP details associated with the email
            otp_details = OTPDetails.objects.get(email=email)
            if otp_details.otp == otp:
                # OTP verified, send username and original password to the user via email
                # Note: Use a local variable to store the plain password temporarily
                plain_password = CustomUser.objects.get(id=user_id).plain_password
                # user.email_user(
                #     subject="Your Account Details",
                #     message=f"Your username is {user.username} and your password is {plain_password}.",
                # )
                # Render email content from the HTML template
                html_message = render_to_string('pass.html', {'email': user.email, 'password':plain_password})
                
                # Send the OTP email with only the HTML template
                send_mail(
                    subject="Credentials for MantraPOS",
                    message="",  # Leave the plain message empty
                    from_email=None,  # Use default email settings or configure as needed
                    recipient_list=[user.email],
                    html_message=html_message  # Only HTML version is provided
                )
                
                otp_details.otp= None
                otp_details.save()
                
                # Clear the plain_password field after sending the email
                user.plain_password = None
                user.verified = True
                user.save()
                
                # Render email content from the HTML template
                html_message = render_to_string('signup.html')
                
                # Send the OTP email with only the HTML template
                send_mail(
                    subject="Welcome to MantraPOS",
                    message="",  # Leave the plain message empty
                    from_email=None,  # Use default email settings or configure as needed
                    recipient_list=[user.email],
                    html_message=html_message  # Only HTML version is provided
                )
                
                return Response({"error": False, "detail": "OTP verified successfully. Username and password have been sent to your email."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": True, "detail": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({"error": True, "detail": "User not found."}, status=status.HTTP_400_BAD_REQUEST)
        except OTPDetails.DoesNotExist:
            return Response({"error": True, "detail": "No OTP record found for this email."}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({"error": True, "detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)







@swagger_auto_schema(
    method="post",
    request_body=CustomUserLoginSerializer,
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
            serializer = CustomUserLoginSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data["user"]
                token, _ = Token.objects.get_or_create(user=user)

                # Generate slug from first name and last name
                slug = (user.first_name + user.last_name).lower().replace(" ", "")

                # Get additional user details
                user_details = {
                    "id": user.id,
                    "username": user.username,
                    "name": user.first_name + " " + user.last_name,
                    "email": user.email,
                    "slug": slug,
                    }
                
                
                # Get company details if available
                if user.company_id:
                    company = Company.objects.get(id=user.company_id)
                    user_details["company"] = {
                        "id": company.id,
                        "name": company.name,
                        "address": company.address,
                        "number_of_outlets": company.number_of_outlets,
                        "number_of_employees": company.number_of_employees,
                        # Add more fields as needed
                    }
                    
                # Get user's active plan details if available
                try:
                    active_plan = PlanAssignment.objects.filter(user=user).latest('valid_till')
                    user_details["plan"] = {
                        "plan_name": active_plan.plan.plan_name,
                        "plan_price": active_plan.plan.plan_price,
                        "price_tenure": active_plan.plan.price_tenure,
                        "valid_till": active_plan.valid_till,
                        "status": active_plan.status,
                    }
                except PlanAssignment.DoesNotExist:
                    user_details["plan"] = None  # No active plan assigned

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





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
                    "role": user.role,
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
                        "price_tenure": active_plan.plan.price_tenure.capitalize(),
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

from django.contrib.auth import get_user_model

User = get_user_model()




@swagger_auto_schema(
    method='patch',
    operation_summary="Reset user password",
    operation_description="Reset password using user_id from URL and new_password from request body",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['new_password'],
        properties={
            'new_password': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='New password (min 6 characters)'
            )
        }
    ),
    responses={
        200: openapi.Response(
            description="Password reset successful",
            examples={
                "application/json": {
                    "error": False,
                    "message": "Password reset successfully"
                }
            }
        ),
        400: openapi.Response(
            description="Validation error",
            examples={
                "application/json": {
                    "error": True,
                    "message": "New password is required"
                }
            }
        ),
        404: openapi.Response(
            description="User not found",
            examples={
                "application/json": {
                    "error": True,
                    "message": "User not found"
                }
            }
        )
    }
)
@api_view(['PATCH'])
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({
            "error": True,
            "message": "User not found"
        }, status=status.HTTP_404_NOT_FOUND)

    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    # 🔥 Validate fields
    if not old_password:
        return Response({
            "error": True,
            "message": "Old password is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    if not new_password:
        return Response({
            "error": True,
            "message": "New password is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    # 🔥 Verify old password
    if not user.check_password(old_password):
        return Response({
            "error": True,
            "message": "Old password is incorrect"
        }, status=status.HTTP_400_BAD_REQUEST)

    # 🔥 Password validation
    if len(new_password) < 6:
        return Response({
            "error": True,
            "message": "Password must be at least 6 characters"
        }, status=status.HTTP_400_BAD_REQUEST)

    # 🔥 Prevent same password reuse
    if old_password == new_password:
        return Response({
            "error": True,
            "message": "New password cannot be same as old password"
        }, status=status.HTTP_400_BAD_REQUEST)

    # 🔥 Set new password
    user.set_password(new_password)

    # Optional: storing plain password (NOT recommended in production)
    user.plain_password = new_password

    user.save()

    return Response({
        "error": False,
        "message": "Password reset successfully"
    }, status=status.HTTP_200_OK)


# ==========================================
# Admin Password Change API
# ==========================================
@swagger_auto_schema(
    method='patch',
    operation_summary="Change Password (Admin)",
    operation_description="Change a user's password from admin panel without needing the old password.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['new_password'],
        properties={
            'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='New password (min 6 chars)')
        }
    ),
    responses={
        200: openapi.Response(description="Password changed successfully"),
        400: openapi.Response(description="Validation error"),
        404: openapi.Response(description="User not found")
    }
)
@api_view(['PATCH'])
@permission_classes([AllowAny])
def admin_change_password(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": True, "message": "User not found"}, status=404)

    new_password = request.data.get('new_password')
    if not new_password or len(new_password) < 6:
        return Response({"error": True, "message": "New password must be at least 6 characters"}, status=400)

    user.set_password(new_password)
    user.plain_password = new_password  # Following existing pattern
    user.save()

    return Response({"error": False, "message": "Password changed successfully"})


# ==========================================
# Forgot Password Flow
# ==========================================
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from email.mime.image import MIMEImage
import os

@swagger_auto_schema(
    method='post',
    operation_summary="Forgot Password",
    operation_description="Initiates password reset flow by sending an email link.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['email'],
        properties={'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL)}
    )
)
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    if request.method == 'GET':
        return render(request, 'forgot_password.html', {'error_msg': None, 'success_msg': None})

    email = request.data.get('email') or request.POST.get('email')
    if not email:
        if request.content_type != 'application/json':
            return render(request, 'forgot_password.html', {'error_msg': 'Email is required', 'success_msg': None})
        return Response({"error": True, "message": "Email is required"}, status=400)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Prevent email enumeration by returning a success-like message anyway
        if request.content_type != 'application/json':
            return render(request, 'forgot_password.html', {'error_msg': None, 'success_msg': 'If this email is registered, a reset link has been sent.'})
        return Response({"error": False, "message": "If this email is registered, a reset link has been sent."}, status=200)

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = PasswordResetTokenGenerator().make_token(user)
    
    # Build URL. For testing locally, request.build_absolute_uri will use the server's domain/port
    reset_url = request.build_absolute_uri(f"/v1/auth/reset-password-confirm/?uid={uid}&token={token}")

    subject = "Password Reset Request"
    text_content = f"Hello {user.username},\n\nPlease click the link below to reset your password:\n\n{reset_url}\n\nIf you did not request this, please ignore this email."
    
    html_content = render_to_string('forgot_password_email.html', {
        'username': user.username,
        'reset_url': reset_url,
    })
    
    try:
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            getattr(settings, 'EMAIL_HOST_USER', 'noreply@mantrapos.com'),
            [user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        # Attach Mantra Logo inline
        mantra_logo_path = os.path.join(settings.BASE_DIR, 'static', 'mantra-logo-white.png')
        if os.path.exists(mantra_logo_path):
            with open(mantra_logo_path, 'rb') as img:
                logo_img = MIMEImage(img.read())
                logo_img.add_header('Content-ID', '<mantra_logo>')
                msg.attach(logo_img)
                
        # Attach Vibrant Logo inline
        vibrant_logo_path = os.path.join(settings.BASE_DIR, 'static', 'vibrant-logo.png')
        if os.path.exists(vibrant_logo_path):
            with open(vibrant_logo_path, 'rb') as img:
                vib_img = MIMEImage(img.read())
                vib_img.add_header('Content-ID', '<vibrant_logo>')
                msg.attach(vib_img)

        msg.send()
    except Exception as e:
        print(f"Email failed to send: {e}")
        # We proceed anyway, maybe it prints to console if misconfigured

    if request.content_type != 'application/json':
        return render(request, 'forgot_password.html', {'error_msg': None, 'success_msg': 'If this email is registered, a reset link has been sent.'})
    return Response({"error": False, "message": "If this email is registered, a reset link has been sent."}, status=200)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def reset_password_confirm(request):
    """
    Renders the HTML form on GET and processes it on POST.
    """
    # 1. Handle HTML GET Request
    if request.method == 'GET':
        uid = request.GET.get('uid', '')
        token = request.GET.get('token', '')

        # Basic HTML template for the reset form
        return render(request, 'reset_password.html', {'uid': uid, 'token': token, 'error_msg': None})

    # 2. Handle HTML Form POST Request
    elif request.method == 'POST':
        uid = request.data.get('uid') or request.POST.get('uid')
        token = request.data.get('token') or request.POST.get('token')
        new_password = request.data.get('new_password') or request.POST.get('new_password')
        confirm_password = request.data.get('confirm_password') or request.POST.get('confirm_password')

        error_msg = None

        if not uid or not token:
            error_msg = "Invalid or missing reset link."
        elif new_password != confirm_password:
            error_msg = "Passwords do not match."
        elif len(new_password) < 6:
            error_msg = "Password must be at least 6 characters."

        user = None
        if not error_msg:
            try:
                user_id = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(pk=user_id)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                error_msg = "Invalid reset link."

        if user and not error_msg:
            if not PasswordResetTokenGenerator().check_token(user, token):
                error_msg = "Reset link has expired or is invalid."

        if error_msg:
            # Re-render form with error
            return render(request, 'reset_password.html', {'uid': uid, 'token': token, 'error_msg': error_msg})

        # Success!
        user.set_password(new_password)
        user.plain_password = new_password
        user.save()

        # Success Page with Redirect
        return render(request, 'reset_password_success.html')


import random

from django.shortcuts import render
from django.core.mail import send_mail

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token

from .serializers import ( 
    CustomUserCounterLoginSerializer
)

from users.models import CustomUser
from v1.models import (
    Company,
    Outlet,
    OutletAccess
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
                    "name": user.first_name + " " + user.last_name,
                    "email": user.email,
                    "slug": slug,
                }

                # Get the list of companies the user is associated with
                companies = Company.objects.filter(outlets__outletaccess__user=user).distinct()
                user_details["companies"] = []

                for company in companies:
                    # Get the outlets the user has access to within this company
                    outlets_access = OutletAccess.objects.filter(user=user, outlet__company=company)
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
                        "number_of_outlets": company.number_of_outlets,
                        "number_of_employees": company.number_of_employees,
                        "outlets": outlets,  # Outlets that the user has access to in this company
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
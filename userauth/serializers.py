from rest_framework import serializers
from v1.models import (
    Company,
    Plan,
    PlanAssignment,
    Outlet,
    OutletAccess,
    Employee
)
from users.models import CustomUser
from datetime import date, timedelta

import random
import string

def generate_random_password(length=10):
    characters = (
        string.ascii_letters +   # a-zA-Z
        string.digits +          # 0-9
        "!@#$%^&*()_+"           # special chars
    )
    return ''.join(random.choice(characters) for _ in range(length))


class CompanyUserSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    number_of_outlets = serializers.IntegerField()
    number_of_employees = serializers.IntegerField()
    phone_number = serializers.CharField(max_length=15)
    verified = serializers.BooleanField(default=False)
    plan_name = serializers.CharField(max_length=50, required=False, default="Free")

    def create(self, validated_data):
        # Replace spaces with underscores in the company name to generate the username
        username = validated_data['company_name'].lower().replace(" ", "_")

        # Create the Company with only name and number_of_outlets
        company = Company.objects.create(
            name=validated_data['company_name'],
            number_of_outlets=validated_data['number_of_outlets'],
            number_of_employees=validated_data['number_of_employees']
        )
        
        # Generate a strong password
        password = generate_random_password()

        # Create the CustomUser with the hashed password
        user = CustomUser.objects.create_user(
            username=username,
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            verified=validated_data['verified'],
            company=company,
            password=password
        )

        # Store the plain password in the `plain_password` field
        user.plain_password = password
        user.role = 'manager'
        user.save()  # Save the user instance to update the plain_password and role fields

        
        # Assign the requested plan to the user
        plan_name = validated_data.get('plan_name', 'Free')
        try:
            assigned_plan = Plan.objects.get(plan_name__iexact=plan_name)
            PlanAssignment.objects.create(
                plan=assigned_plan,
                user=user,
                valid_till=date.today() + timedelta(days=15),  # Valid for 15 days from today
                status='active'
            )
        except Plan.DoesNotExist:
            raise serializers.ValidationError(f"Plan '{plan_name}' is not available.")
        
        
        
        # Create an entry in the Employee model with the role of 'manager'
        Employee.objects.create(
            company=company,
            user=user,
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            role='manager'
        )
        
        
        return user




class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    
    
    
class OTPVerificationSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)
    
    
    
    
class CustomUserLoginSerializer(serializers.Serializer):
    username = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.CharField(required=True)

    def validate(self, data):
        email = data.get('username')
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError("Email and password are required.")

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        # Check if the password matches
        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password.")

        role = data.get('role')
        if user.role != role:
            raise serializers.ValidationError(f"Access denied: User does not have the '{role}' role.")

        data['user'] = user
        return data    




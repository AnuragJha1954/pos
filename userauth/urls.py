from django.urls import path
from .views import create_user, resend_otp,verify_otp, user_login, reset_password

urlpatterns = [
    path('sign-up/', create_user, name='User Sign up'),
    path('resend-otp/<int:user_id>/', resend_otp, name='Rsend OTP to Email'),
    path('verify-otp/<int:user_id>/', verify_otp, name='OTP Verfication'),
    path('login/', user_login, name="Login Method"),
    path('reset-password/<int:user_id>/', reset_password, name='reset_password'),
]

from django.urls import path
from .views import (
    create_user, resend_otp, verify_otp, user_login, 
    reset_password, forgot_password, reset_password_confirm,
    admin_change_password
)


urlpatterns = [
    path('sign-up/', create_user, name='User Sign up'),
    path('resend-otp/<int:user_id>/', resend_otp, name='Rsend OTP to Email'),
    path('verify-otp/<int:user_id>/', verify_otp, name='OTP Verfication'),
    path('login/', user_login, name="Login Method"),
    path('change-password/<int:user_id>/', reset_password, name='change_password'),
    path('admin/change-password/<int:user_id>/', admin_change_password, name='admin_change_password'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('reset-password-confirm/', reset_password_confirm, name='reset_password_confirm'),
]

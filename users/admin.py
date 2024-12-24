from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


# Register your models here.


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'phone_number', 'verified', 'company')
    search_fields = ('username', 'email', 'phone_number')
    list_filter = ('verified', 'company')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'company','plain_password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone_number', 'company', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )

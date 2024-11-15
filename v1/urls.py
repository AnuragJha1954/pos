from django.urls import path
from . import views

urlpatterns = [
    
    # Outlet related URLs
    path('create_outlet/<int:company_id>/<int:user_id>/', views.create_outlet, name='create_outlet'),
    
    # Grant outlet access URLs
    path('grant_outlet_access/<int:outlet_id>/<int:user_id>/<int:manager_id>/', views.grant_outlet_access, name='grant_outlet_access'),
    
    # Employee related URLs
    path('create_employee/<int:user_id>/', views.create_employee, name='create_employee'),
    path('update_profile/<int:employee_id>/<int:user_id>/', views.update_profile, name='update_profile'),

    
    # Product related URLs
    path('add_product/<int:user_id>/', views.add_product, name='add_product'),
    path('add_product_variant/<int:user_id>/', views.add_product_variant, name='add_product_variant'),
    path('get_products/<int:outlet_id>/', views.get_products, name='get_products'),
    
    # Menu related URLs
    path('add_menu/<int:user_id>/', views.add_menu, name='add_menu'),
    path('get_outlet_menus/<int:outlet_id>/<int:user_id>/', views.get_outlet_menus, name='get_outlet_menus'),
    path('get_menu_details/<int:menu_id>/', views.get_menu_details, name='get_menu_details'),
    
    # Category related URLs
    path('add_category/<int:outlet_id>/<int:user_id>/', views.add_category, name='add_category'),
    path('categories/<int:outlet_id>/<int:user_id>/', views.get_categories_by_outlet, name='get_categories_by_outlet'),
    
    # Stock request related URLs
    path('stock-requests/<int:user_id>/<int:outlet_id>/pending/', views.get_pending_stock_requests, name='get_pending_stock_requests'),
    path('stock-requests/<int:user_id>/<int:outlet_id>/approve/', views.approve_stock_requests, name='approve_stock_requests'),

]
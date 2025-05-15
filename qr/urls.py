from django.urls import path
from .views import (
    category_list,
    product_list,
    place_order,
    random_products,
    get_banners,
    active_coupons,
    get_razorpay_credentials,
    get_outlet_details
)

urlpatterns = [
    path('get-categories/<int:outlet_id>/', category_list, name='category-list'),
    path('get-products/<int:outlet_id>/', product_list, name='product_list'),
    path('place-order/<int:outlet_id>/', place_order, name='place_order'),
    path('special-menu/<int:outlet_id>/', random_products, name='random_products'),
    path('get-advertisement-banners/<int:outlet_id>/', get_banners, name='get_banners'),
    path('get-coupons/<int:outlet_id>/', active_coupons, name='active-coupons'),
    path('razorpay/<int:outlet_id>/', get_razorpay_credentials, name='get_razorpay_credentials'),
    path('get-outlet-details/<int:outlet_id>/', get_outlet_details, name='get_outlet_details'),
]
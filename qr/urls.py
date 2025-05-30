from django.urls import path
from .views import (
    category_list,
    product_list,
    place_order,
    get_special_menu,
    get_banners,
    active_coupons,
    get_razorpay_credentials,
    get_outlet_details,
    add_or_update_razorpay_credentials,
    add_or_update_qr_customization,
    add_advertisement_banner,
    add_special_menu,
    update_special_menu_name,
    generate_table_qrs
)

urlpatterns = [
    path('get-categories/<int:outlet_id>/', category_list, name='category-list'),
    path('get-products/<int:outlet_id>/', product_list, name='product_list'),
    path('place-order/<int:outlet_id>/', place_order, name='place_order'),
    path('special-menu/<int:outlet_id>/', get_special_menu, name='get_special_menu'),
    path('get-advertisement-banners/<int:outlet_id>/', get_banners, name='get_banners'),
    path('add-advertisement-banners/<int:outlet_id>/', add_advertisement_banner, name='add-advertisement-banner'),
    path('get-coupons/<int:outlet_id>/', active_coupons, name='active-coupons'),
    path('razorpay/<int:outlet_id>/', get_razorpay_credentials, name='get_razorpay_credentials'),
    path('razorpay/add/<int:outlet_id>/', add_or_update_razorpay_credentials, name='razorpay-credential'),
    path('get-outlet-details/<int:outlet_id>/', get_outlet_details, name='get_outlet_details'),
    path('qr-customization/add/<int:outlet_id>/', add_or_update_qr_customization, name='qr-customization'),
    path('special-menu/add/<int:outlet_id>/', add_special_menu, name='add-special-menu'),
    path('special-menu/update-name/<int:outlet_id>/', update_special_menu_name, name='update_special_menu_name'),
    path('generate-qr/<int:outlet_id>/', generate_table_qrs, name='generate_table_qrs'),

]
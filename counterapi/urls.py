from django.urls import path
from .views import (
    user_login,
    category_list,
    product_list,
    place_order,
    orders_past_three_hours,
    order_details,
    create_stock_request,
    print_kot
    )

urlpatterns = [
    # Endpoint to login into the counter
    path('login/', user_login, name="Login Method Counter"),
    
    # Endpoint to fetch the list of categories
    path('<int:outlet_id>/get-categories/', category_list, name='Get Categories for Counter'),
    
    # Endpoint to fetch the list of products
    path('products/', product_list, name='product_list'),

    # Endpoint to place an order, passing outlet_id in the URL
    path('orders/<int:outlet_id>/place-order/', place_order, name='place_order'),

    path('orders/<int:outlet_id>/print-kot/', print_kot, name='print_kot'),

    # Endpoint to fetch orders placed in the past 3 hours, passing outlet_id in the URL
    path('orders/<int:outlet_id>/get-orders/', orders_past_three_hours, name='orders_past_three_hours'),

    # Endpoint to get order details by order number, passing outlet_id in the URL
    path('orders/<int:outlet_id>/order-details/', order_details, name='order_details'),

    # Endpoint to create a stock request, passing outlet_id in the URL
    path('stock-requests/<int:outlet_id>/stock-requests/', create_stock_request, name='create_stock_request'),
    
]

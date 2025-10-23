from django.urls import path
from .views import (
    user_login,
    category_list,
    product_list,
    place_order,
    orders_past_three_hours,
    order_details,
    create_stock_request,
    print_kot,
    mark_items_stock_out,
    send_order_notification,
    upload_billed_transaction,
    get_transaction_status,
    cancel_transaction
    )

urlpatterns = [
    # Endpoint to login into the counter
    path('login/', user_login, name="Login Method Counter"),
    
    # Endpoint to fetch the list of categories
    path('<int:outlet_id>/get-categories/', category_list, name='Get Categories for Counter'),
    
    # Endpoint to fetch the list of products
    path('<int:outlet_id>/products/', product_list, name='product_list'),

    # Endpoint to place an order, passing outlet_id in the URL
    path('orders/<int:outlet_id>/place-order/', place_order, name='place_order'),
    
    path('orders/<int:outlet_id>/print-kot/', print_kot, name='print_kot'),

    # Endpoint to fetch orders placed in the past 3 hours, passing outlet_id in the URL
    path('orders/<int:outlet_id>/get-orders/', orders_past_three_hours, name='orders_past_three_hours'),

    # Endpoint to get order details by order number, passing outlet_id in the URL
    path('orders/<int:outlet_id>/order-details/', order_details, name='order_details'),

    # Endpoint to create a stock request, passing outlet_id in the URL
    path('stock-requests/<int:outlet_id>/stock-requests/', create_stock_request, name='create_stock_request'),
    
    # Endpoint to mark items as stock out
    path('stock-out/<int:outlet_id>/mark-stock-out/', mark_items_stock_out, name='mark-stock-out'),
    path('test/', send_order_notification, name='send_order_notification'),
    
    path("initiate-transaction/<int:user_id>/<str:order_number>/", upload_billed_transaction, name="upload_billed_transaction"),
    path("get-transaction-status/<int:user_id>/", get_transaction_status, name="get_transaction_status"),
    path("cancel-transaction/<int:user_id>/", cancel_transaction, name="cancel_transaction"),
    
]

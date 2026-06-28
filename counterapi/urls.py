from django.urls import path
from .views import (
    add_expense,
    get_expenses,
    get_expenses,
    get_table_with_kot,
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
    cancel_transaction,
    get_tables_by_outlet,
    update_table_status,
    add_items_to_order,
    update_order_item_status,
    bulk_update_order_items,
    settle_order,
    check_payment_status,
    confirm_payment,
    change_order_status,
    delete_draft_order,

    )

urlpatterns = [
    # Endpoint to fetch the list of categories
    path('<int:outlet_id>/get-categories/', category_list, name='Get Categories for Counter'),
    
    # Endpoint to fetch the list of products
    path('<int:outlet_id>/products/', product_list, name='product_list'),

    # Endpoint to place an order, passing outlet_id in the URL
    path('orders/<int:outlet_id>/place-order/', place_order, name='place_order'),
    
    path('orders/<str:order_number>/print-kot/', print_kot, name='print_kot'),

    # Endpoint to fetch orders placed in the past 3 hours, passing outlet_id in the URL
    path('orders/<int:outlet_id>/get-orders/', orders_past_three_hours, name='orders_past_three_hours'),

    # Endpoint to get order details by order number, passing outlet_id in the URL
    path('orders/<int:outlet_id>/order-details/', order_details, name='order_details'),

    # Endpoint to create a stock request, passing outlet_id in the URL
    path('stock-requests/<int:outlet_id>/stock-requests/', create_stock_request, name='create_stock_request'),
    
    # Endpoint to mark items as stock out
    path('stock-out/<int:outlet_id>/mark-stock-out/', mark_items_stock_out, name='mark-stock-out'),
    path('test/', send_order_notification, name='send_order_notification'),
    
    path("initiate-transaction/<int:user_id>/", upload_billed_transaction, name="upload_billed_transaction"),
    path("get-transaction-status/<int:user_id>/", get_transaction_status, name="get_transaction_status"),
    path("cancel-transaction/<int:user_id>/", cancel_transaction, name="cancel_transaction"),
    
    path('outlet/<int:outlet_id>/tables/', get_tables_by_outlet),
    path('tables/<int:table_id>/status/', update_table_status),
    path('tables/<str:table_id>/<int:outlet_id>/details/', get_table_with_kot, name='table-with-kot'),
    
    path('outlet/<int:outlet_id>/expenses/', get_expenses),
    path('outlet/<int:outlet_id>/expenses/add/', add_expense),
    
    
    
    path('order/<int:order_id>/add-items/', add_items_to_order, name='add-items'),
    path('order-item/<int:item_id>/status/', update_order_item_status, name='update-order-item-status'),
    path('order-items/bulk-update/', bulk_update_order_items, name='bulk-update-order-items'),
    path('order/<int:order_id>/settle/', settle_order, name='settle-order'),
    path('orders/<int:order_id>/status/', change_order_status, name='change_order_status'),
    path('orders/<int:order_id>/delete-draft/', delete_draft_order, name='delete_draft_order'),
    
    path('payments/status/',check_payment_status,name='check_payment_status'),
    path('payments/confirm/',confirm_payment,name='confirm_payment'),
    
]

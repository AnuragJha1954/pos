from django.urls import path
from . import views

urlpatterns = [
    
    # Outlet related URLs
    path('outlets/create/<int:company_id>/<int:user_id>/', views.create_outlet, name='create_outlet'),
    path('outlets/list/<int:company_id>/<int:user_id>/', views.list_company_outlets,name='list_company_outlets'),
    path('outlets/get-detail/<int:outlet_id>/<int:user_id>/', views.get_outlet_detail, name='get_outlet_detail'),
    path('outlets/update/<int:outlet_id>/<int:user_id>/', views.update_outlet, name='update_outlet'),
    path('outlets/delete/<int:outlet_id>/<int:user_id>/', views.delete_outlet, name='delete_outlet'),
    
    # Grant outlet access URLs
    path('grant_outlet_access/<int:outlet_id>/<int:user_id>/<int:manager_id>/', views.grant_outlet_access, name='grant_outlet_access'),
    
    # Employee related URLs
    path('create_employee/<int:user_id>/', views.create_employee, name='create_employee'),
    path('update_profile/<int:employee_id>/<int:user_id>/', views.update_profile, name='update_profile'),
    path('get-employees/<int:user_id>/', views.get_employees_by_user, name='get_employees_by_user'),
    path('update-permissions/<int:user_id>/<int:employee_id>/', views.update_employee_permissions, name='update_employee_permissions'),
    path('get-credentials/<int:employee_id>/<int:user_id>/', views.get_employee_credentials, name='get_employee_credentials'),
    path('manage-credentials/<int:employee_id>/<int:user_id>/', views.manage_employee_credentials, name='manage_employee_credentials'),
    path('employees/<int:employee_id>/toggle-status/', views.toggle_employee_status, name='toggle-employee-status'),

    
    # Product related URLs
    path('add_product/<int:user_id>/', views.add_product, name='add_product'),
    path('add_product_variant/<int:user_id>/', views.add_product_variant, name='add_product_variant'),
    path('add_product_with_variant/<int:user_id>/', views.add_product_with_variants, name='add_product_with_variants'),
    path('get_products/<int:outlet_id>/', views.get_products, name='get_products'),
    path("edit-product/<int:user_id>/<int:product_id>/", views.edit_product, name="edit_product"),
    path("delete-product/<int:user_id>/<int:product_id>/", views.delete_product, name="delete_product"),
    path("edit-variant/<int:user_id>/<int:variant_id>/", views.edit_product_variant, name="edit_product_variant"),
    path("delete-variant/<int:user_id>/<int:variant_id>/", views.delete_product_variant, name="delete_product_variant"),
    
    # Menu related URLs
    path('add_menu/<int:user_id>/', views.add_menu, name='add_menu'),
    path('get_outlet_menus/<int:outlet_id>/<int:user_id>/', views.get_outlet_menus, name='get_outlet_menus'),
    path('get_menu_details/<int:menu_id>/', views.get_menu_details, name='get_menu_details'),
    path("edit-menu/<int:user_id>/<int:menu_id>/", views.edit_menu, name="edit_menu"),
    path("duplicate-menu/<int:user_id>/<int:menu_id>/", views.duplicate_menu, name="duplicate_menu"),
    path("toggle-menu/<int:user_id>/<int:menu_id>/", views.toggle_menu, name="toggle_menu"),
    path("add-products-in-menu/<int:user_id>/<int:menu_id>/", views.add_products_to_menu, name="add_products_to_menu"),
    path("remove-products-from-menu/<int:user_id>/<int:menu_id>/", views.remove_products_from_menu, name="remove_products_from_menu"),
    path("get-menu-products/<int:user_id>/<int:menu_id>/products/", views.get_menu_products, name="get_menu_products"),
    
    # Category related URLs
    path('add_category/<int:outlet_id>/<int:user_id>/', views.add_category, name='add_category'),
    path('categories/<int:outlet_id>/<int:user_id>/', views.get_categories_by_outlet, name='get_categories_by_outlet'),
    path('categories/edit/<int:outlet_id>/<int:user_id>/<int:category_id>/', views.edit_category),
    path('categories/delete/<int:outlet_id>/<int:user_id>/<int:category_id>/', views.delete_category),
    
    # Stock request related URLs
    path('stock-requests/<int:user_id>/<int:outlet_id>/pending/', views.get_pending_stock_requests, name='get_pending_stock_requests'),
    path('stock-requests/<int:user_id>/<int:outlet_id>/approve/', views.approve_stock_requests, name='approve_stock_requests'),
    
    
    # Order related URLs
    path('get-orders-list/<int:company_id>/', views.get_company_orders, name='company-orders'),
    path('get-order-details/<str:order_number>/', views.get_order_details_by_number, name='get_order_details_by_number'),
    path('genrate-bill/<str:order_number>/', views.generate_order_bill, name='generate_order_bill'),
    path('cancel-order/<str:order_number>/', views.cancel_order, name='cancel-order'),
    
    #Refund Note related Urls
    path('refund-note/<str:order_number>/add/', views.add_refund_note, name='add-refund-note'),
    path('refund-note/<str:order_number>/get/', views.get_refund_notes_by_order, name='get-refund-notes'),
    
    #Customer Related Urls
    path('get-customers/<int:company_id>/',views.list_company_customers,name='list_company_customers'),
    
        # -------- DASHBOARD (OUTLET LEVEL) --------
    path("dashboard/", views.dashboard_data, name="dashboard"),

    # -------- REPORTS (OUTLET LEVEL) --------
    path("reports/<int:outlet_id>/sales/", views.sales_report_sample, name="sales-report"),
    path("reports/<int:outlet_id>/orders/", views.orders_report_sample, name="orders-report"),
    path("reports/<int:outlet_id>/customers/", views.customers_report_sample, name="customers-report"),

    # -------- COMPANY REPORT (OUTLET SUMMARY) --------
    
    #Printer Config
    path("printer-config/<int:outlet_id>/", views.set_printer_config, name="set-printer-config"),
    path("printer-config/<int:outlet_id>/get/", views.get_printer_config, name="get-printer-config"),
    
    path('plan/update/', views.update_user_plan, name='update_user_plan'),
    
    
    # TABLE
    path('tables/create/', views.create_table),
    path('tables/<int:outlet_id>/', views.get_tables),
    path('tables/update/<int:table_id>/', views.update_table),
    path('tables/<int:table_id>/update-status/',views.update_table_status,name='update-table-status'),

    # EXPENSE
    path('expenses/create/', views.create_expense),
    path('expenses/<int:outlet_id>/', views.get_expenses),
    path('expenses/update/<int:expense_id>/', views.update_expense),

    
    
    # Reports
    path('reports/daily/', views.daily_sales_report),
    path('reports/outlet/', views.outlet_sales_report),
    path('reports/hourly/', views.hourly_sales_report),
    path('reports/order-status/', views.order_status_report),
    path('reports/payment-status/', views.payment_status_report),
    path('reports/payment-mode/', views.payment_mode_analysis),
    path('reports/pending/', views.pending_payments_report),
    path('reports/top-products/', views.top_products),
    path('reports/product-revenue/', views.product_revenue),
    path('reports/variant/', views.variant_performance),
    path('reports/category/', views.category_sales),
    path('reports/veg-nonveg/', views.veg_nonveg),
    path('reports/kot-volume/', views.kot_volume),
    path('reports/table-kot/', views.table_kot),
    path('reports/kitchen/', views.kitchen_efficiency),
    path('reports/kot-turnaround/', views.kot_turnaround),
    path('reports/table-turnover/', views.table_turnover),
    path('reports/table-utilization/', views.table_utilization),
    path('reports/expense/', views.expense_vs_revenue),
    path('reports/refund/', views.refund_analysis),
    path('reports/customer-repeat/', views.customer_repeat_report, name='customer_repeat_report'),
    path('reports/avg-order-value/', views.avg_order_value_trend, name='avg_order_value_trend'),
    path('reports/peak-days/', views.peak_days_report, name='peak_days_report'),
    path('reports/coupon-impact/', views.coupon_impact_report, name='coupon_impact_report'),
    path('reports/stockout-impact/', views.stockout_impact_report, name='stockout_impact_report'),

]
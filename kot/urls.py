from django.urls import path
from . import views

urlpatterns = [
    path('orders/<int:outlet_id>/', views.get_orders_for_kot, name='get_orders_for_kot'),
    path('orders/<int:order_id>/status/process/', views.change_order_status_to_processing, name='change_order_status_to_processing'),
    path('orders/<int:order_id>/status/complete/', views.change_order_status_to_completed, name='change_order_status_to_completed'),
    path('register-fcm/<int:outlet_id>/', views.register_fcm_token, name='register_fcm_token'),
    
    path('kot-login/', views.kot_login, name='kot-login'),
    path('kot-device/deregister/', views.deregister_kot_device, name='kot-device-deregister'),
    path('kot/check-status/', views.check_kot_status, name='kot-status'),
]

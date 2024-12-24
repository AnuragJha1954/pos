from django.urls import path
from . import views

urlpatterns = [
    path('orders/', views.get_orders_for_kot, name='get_orders_for_kot'),
    path('orders/<int:order_id>/status/process/', views.change_order_status_to_processing, name='change_order_status_to_processing'),
    path('orders/<int:order_id>/status/complete/', views.change_order_status_to_completed, name='change_order_status_to_completed'),
]

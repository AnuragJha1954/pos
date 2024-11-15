from django.urls import path
from . import views

urlpatterns = [
    # Endpoint to create a ticket
    path('tickets/create/<int:user_id>/<int:outlet_id>/', views.create_ticket, name='create-ticket'),
    
    # Endpoint to list tickets for a specific outlet
    path('tickets/<int:outlet_id>/', views.list_tickets, name='ticket-list'),
]

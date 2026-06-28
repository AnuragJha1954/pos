from django.urls import path
from . import views

urlpatterns = [
    path('create-order/', views.create_subscription_order, name='create_subscription_order'),
    path('verify-payment/', views.verify_subscription_payment, name='verify_subscription_payment'),
    path('docs/', views.subscription_flow_docs, name='subscription_flow_docs'),
]

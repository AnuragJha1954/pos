from django.urls import path
from .views import (
    category_list,
    product_list,
    place_order
)

urlpatterns = [
    path('get-categories/<int:outlet_id>/', category_list, name='category-list'),
    path('get-products/<int:outlet_id>/', product_list, name='product_list'),
    path('place-order/<int:outlet_id>/', place_order, name='place_order'),
]
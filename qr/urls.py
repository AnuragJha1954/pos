from django.urls import path
from .views import (
    category_list,
    product_list,
    place_order
)

urlpatterns = [
    path('get-categories/', category_list, name='category-list'),
    path('get-products/', product_list, name='product_list'),
    path('place-order/', place_order, name='place_order'),
]
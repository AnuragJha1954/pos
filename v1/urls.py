from django.urls import path
from . import views

urlpatterns = [
    path('companies/<int:company_id>/outlets/', views.create_outlet, name='create_outlet'),
    path('outlets/<int:outlet_id>/grant-access/<int:user_id>/', views.grant_access, name='grant_access'),

]
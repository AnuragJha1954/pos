from django.urls import path
from . import views

urlpatterns = [
    # Supplier routes
    path('outlets/<int:outlet_id>/suppliers/', views.list_suppliers, name='list_suppliers'),
    path('outlets/<int:outlet_id>/suppliers/create/', views.create_supplier, name='create_supplier'),
    
    # Inventory Item routes
    path('outlets/<int:outlet_id>/items/', views.list_inventory_items, name='list_inventory_items'),
    path('outlets/<int:outlet_id>/items/create/', views.create_inventory_item, name='create_inventory_item'),
    
    # Stock Transaction routes
    path('transactions/add/', views.add_stock_transaction, name='add_stock_transaction'),
    path('items/<int:item_id>/transactions/', views.list_stock_transactions, name='list_stock_transactions'),
    
    # Manual Workflow routes
    path('mark-out-of-stock/', views.mark_out_of_stock, name='mark_out_of_stock'),
    path('restock/', views.restock, name='restock'),
]

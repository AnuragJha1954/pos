from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Supplier, InventoryItem, StockTransaction
from .serializers import (
    SupplierSerializer, 
    InventoryItemSerializer, 
    StockTransactionSerializer,
    MarkStockOutInputSerializer,
    RestockInputSerializer
)
from v1.models import Outlet

# =======================
# SUPPLIER APIs
# =======================

@swagger_auto_schema(
    method='get',
    responses={200: SupplierSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_suppliers(request, outlet_id):
    try:
        outlet = Outlet.objects.get(id=outlet_id)
        suppliers = Supplier.objects.filter(outlet=outlet)
        serializer = SupplierSerializer(suppliers, many=True)
        return Response({
            'error': False,
            'details': 'Suppliers retrieved successfully',
            'suppliers': serializer.data
        }, status=status.HTTP_200_OK)
    except Outlet.DoesNotExist:
        return Response({'error': True, 'details': 'Outlet not found'}, status=status.HTTP_404_NOT_FOUND)

@swagger_auto_schema(
    method='post',
    request_body=SupplierSerializer,
    responses={201: SupplierSerializer}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_supplier(request, outlet_id):
    try:
        outlet = Outlet.objects.get(id=outlet_id)
    except Outlet.DoesNotExist:
        return Response({'error': True, 'details': 'Outlet not found'}, status=status.HTTP_404_NOT_FOUND)
        
    data = request.data.copy()
    data['outlet'] = outlet.id
    serializer = SupplierSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'error': False,
            'details': 'Supplier created successfully',
            'supplier': serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response({'error': True, 'details': str(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)

# =======================
# INVENTORY ITEM APIs
# =======================

@swagger_auto_schema(
    method='get',
    responses={200: InventoryItemSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_inventory_items(request, outlet_id):
    try:
        outlet = Outlet.objects.get(id=outlet_id)
        items = InventoryItem.objects.filter(outlet=outlet)
        serializer = InventoryItemSerializer(items, many=True)
        return Response({
            'error': False,
            'details': 'Inventory items retrieved successfully',
            'inventory_items': serializer.data
        }, status=status.HTTP_200_OK)
    except Outlet.DoesNotExist:
        return Response({'error': True, 'details': 'Outlet not found'}, status=status.HTTP_404_NOT_FOUND)

@swagger_auto_schema(
    method='post',
    request_body=InventoryItemSerializer,
    responses={201: InventoryItemSerializer}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_inventory_item(request, outlet_id):
    try:
        outlet = Outlet.objects.get(id=outlet_id)
    except Outlet.DoesNotExist:
        return Response({'error': True, 'details': 'Outlet not found'}, status=status.HTTP_404_NOT_FOUND)
        
    data = request.data.copy()
    data['outlet'] = outlet.id
    serializer = InventoryItemSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'error': False,
            'details': 'Inventory item created successfully',
            'inventory_item': serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response({'error': True, 'details': str(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)

# =======================
# STOCK TRANSACTION APIs
# =======================

@swagger_auto_schema(
    method='post',
    request_body=StockTransactionSerializer,
    responses={201: StockTransactionSerializer}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_stock_transaction(request):
    serializer = StockTransactionSerializer(data=request.data)
    if serializer.is_valid():
        transaction = serializer.save()
        
        # Update current stock
        item = transaction.item
        if transaction.transaction_type in ['purchase', 'return', 'adjustment']:
            item.current_stock += transaction.quantity
        elif transaction.transaction_type in ['sale', 'damage']:
            val = abs(transaction.quantity)
            item.current_stock -= val
            transaction.quantity = -val
            transaction.save()
            
        item.save()
        
        return Response({
            'error': False,
            'details': 'Stock transaction recorded successfully',
            'transaction': StockTransactionSerializer(transaction).data
        }, status=status.HTTP_201_CREATED)
        
    return Response({'error': True, 'details': str(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get',
    responses={200: StockTransactionSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_stock_transactions(request, item_id):
    try:
        item = InventoryItem.objects.get(id=item_id)
        transactions = StockTransaction.objects.filter(item=item).order_by('-created_at')
        serializer = StockTransactionSerializer(transactions, many=True)
        return Response({
            'error': False,
            'details': 'Transactions retrieved successfully',
            'transactions': serializer.data
        }, status=status.HTTP_200_OK)
    except InventoryItem.DoesNotExist:
        return Response({'error': True, 'details': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

# =======================
# WORKFLOW APIs
# =======================

@swagger_auto_schema(
    method='post',
    request_body=MarkStockOutInputSerializer,
    responses={200: openapi.Response("Success message")}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def mark_out_of_stock(request):
    """
    Manually mark multiple inventory items as out of stock.
    Sets quantity to 0 and updates the corresponding Product/Variant is_stock_out flag.
    """
    serializer = MarkStockOutInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'error': True, 'details': str(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
        
    item_ids = serializer.validated_data['item_ids']
    items = InventoryItem.objects.filter(id__in=item_ids)
    
    updated_count = 0
    for item in items:
        # Create an adjustment transaction to 0
        if item.current_stock > 0:
            StockTransaction.objects.create(
                item=item,
                transaction_type='adjustment',
                quantity=-item.current_stock,
                notes='Manual Out of Stock'
            )
            item.current_stock = 0
            item.save()
            
        # Flag v1 Models
        if item.linked_product:
            item.linked_product.is_stock_out = True
            item.linked_product.save()
        if item.linked_variant:
            item.linked_variant.is_stock_out = True
            item.linked_variant.save()
            
        updated_count += 1

    return Response({
        'error': False,
        'details': f'Successfully marked {updated_count} items as out of stock.'
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    request_body=RestockInputSerializer,
    responses={200: openapi.Response("Success message")}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def restock(request):
    """
    Manually restock items. Adds quantity, creates an audit log, 
    and removes the is_stock_out flag on v1 models.
    """
    serializer = RestockInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'error': True, 'details': str(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
        
    restock_items = serializer.validated_data['items']
    
    updated_count = 0
    for r_item in restock_items:
        try:
            item = InventoryItem.objects.get(id=r_item['item_id'])
            supplier_id = r_item.get('supplier_id')
            supplier = Supplier.objects.filter(id=supplier_id).first() if supplier_id else None
            
            # Create transaction
            StockTransaction.objects.create(
                item=item,
                transaction_type='purchase',
                quantity=r_item['quantity'],
                supplier=supplier,
                notes='Manual Restock'
            )
            
            # Update stock
            item.current_stock += r_item['quantity']
            item.save()
            
            # Flag v1 Models
            if item.linked_product:
                item.linked_product.is_stock_out = False
                item.linked_product.save()
            if item.linked_variant:
                item.linked_variant.is_stock_out = False
                item.linked_variant.save()
                
            updated_count += 1
        except InventoryItem.DoesNotExist:
            continue
            
    return Response({
        'error': False,
        'details': f'Successfully restocked {updated_count} items.'
    }, status=status.HTTP_200_OK)

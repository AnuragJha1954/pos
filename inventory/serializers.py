from rest_framework import serializers
from .models import Supplier, InventoryItem, StockTransaction

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = '__all__'

class StockTransactionSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = StockTransaction
        fields = '__all__'

class MarkStockOutInputSerializer(serializers.Serializer):
    item_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of InventoryItem IDs to mark as out of stock."
    )

class RestockItemInputSerializer(serializers.Serializer):
    item_id = serializers.IntegerField(help_text="InventoryItem ID")
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Quantity restocked")
    supplier_id = serializers.IntegerField(required=False, allow_null=True, help_text="Supplier ID (optional)")

class RestockInputSerializer(serializers.Serializer):
    items = RestockItemInputSerializer(many=True, help_text="List of items being restocked")

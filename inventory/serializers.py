"""
Inventory module serializers.
"""

from rest_framework import serializers
from .models import (
    MedicineCategory, Supplier, Medicine, Inventory,
    InventoryTransaction, PurchaseOrder, PurchaseOrderItem, CompoundFormula
)


class MedicineCategorySerializer(serializers.ModelSerializer):
    """藥品分類序列化器"""
    
    class Meta:
        model = MedicineCategory
        fields = ['id', 'name', 'code', 'description', 'parent']


class SupplierSerializer(serializers.ModelSerializer):
    """供應商序列化器"""
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'code', 'contact_person', 'phone', 'fax',
            'email', 'address', 'notes', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class MedicineSerializer(serializers.ModelSerializer):
    """藥品序列化器"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    medicine_type_display = serializers.CharField(source='get_medicine_type_display', read_only=True)
    current_stock = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Medicine
        fields = [
            'id', 'code', 'name', 'english_name', 'pinyin',
            'medicine_type', 'medicine_type_display', 'category', 'category_name',
            'specification', 'unit', 'package_unit', 'package_quantity',
            'brand', 'supplier', 'supplier_name',
            'cost_price', 'selling_price', 'safety_stock',
            'properties', 'meridians', 'functions', 'indications',
            'contraindications', 'dosage_guide', 'external_sku',
            'notes', 'is_active', 'current_stock', 'is_low_stock',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_current_stock(self, obj):
        try:
            return obj.inventory.quantity
        except Inventory.DoesNotExist:
            return 0
    
    def get_is_low_stock(self, obj):
        try:
            return obj.inventory.is_low_stock
        except Inventory.DoesNotExist:
            return False


class MedicineListSerializer(serializers.ModelSerializer):
    """藥品列表序列化器（簡化版）"""
    
    current_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Medicine
        fields = [
            'id', 'code', 'name', 'pinyin', 'medicine_type',
            'unit', 'selling_price', 'current_stock', 'is_active'
        ]
    
    def get_current_stock(self, obj):
        try:
            return obj.inventory.quantity
        except Inventory.DoesNotExist:
            return 0


class InventorySerializer(serializers.ModelSerializer):
    """庫存序列化器"""
    
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    medicine_code = serializers.CharField(source='medicine.code', read_only=True)
    unit = serializers.CharField(source='medicine.unit', read_only=True)
    safety_stock = serializers.DecimalField(
        source='medicine.safety_stock',
        max_digits=10, decimal_places=2, read_only=True
    )
    is_low_stock = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Inventory
        fields = [
            'id', 'medicine', 'medicine_name', 'medicine_code',
            'quantity', 'unit', 'safety_stock', 'is_low_stock', 'last_updated'
        ]


class InventoryTransactionSerializer(serializers.ModelSerializer):
    """庫存異動序列化器"""
    
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = InventoryTransaction
        fields = [
            'id', 'medicine', 'medicine_name',
            'transaction_type', 'transaction_type_display',
            'quantity', 'before_quantity', 'after_quantity',
            'unit_cost', 'reference_number', 'notes',
            'created_at', 'created_by', 'created_by_name'
        ]
        read_only_fields = ['id', 'created_at']


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    """進貨單項目序列化器"""
    
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    medicine_code = serializers.CharField(source='medicine.code', read_only=True)
    
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'medicine', 'medicine_name', 'medicine_code',
            'quantity', 'unit_price', 'subtotal', 'received_quantity'
        ]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """進貨單序列化器"""
    
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'order_number', 'supplier', 'supplier_name',
            'status', 'status_display',
            'order_date', 'expected_date', 'received_date',
            'total_amount', 'notes', 'items',
            'created_at', 'created_by'
        ]
        read_only_fields = ['id', 'order_number', 'created_at']


class PurchaseOrderCreateSerializer(serializers.ModelSerializer):
    """進貨單建立序列化器"""
    
    items = PurchaseOrderItemSerializer(many=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'supplier', 'order_date', 'expected_date', 'notes', 'items'
        ]
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # 生成訂單編號
        from datetime import date
        today = date.today()
        prefix = f"PO{today.strftime('%Y%m%d')}"
        last_order = PurchaseOrder.objects.filter(
            order_number__startswith=prefix
        ).order_by('-order_number').first()
        
        if last_order:
            last_num = int(last_order.order_number[-4:])
            new_num = last_num + 1
        else:
            new_num = 1
        
        validated_data['order_number'] = f"{prefix}{new_num:04d}"
        
        order = PurchaseOrder.objects.create(**validated_data)
        
        total = 0
        for item_data in items_data:
            item = PurchaseOrderItem.objects.create(order=order, **item_data)
            total += item.subtotal
        
        order.total_amount = total
        order.save()
        
        return order


class CompoundFormulaSerializer(serializers.ModelSerializer):
    """複方成份序列化器"""
    
    compound_medicine_name = serializers.CharField(source='compound_medicine.name', read_only=True)
    ingredient_medicine_name = serializers.CharField(source='ingredient_medicine.name', read_only=True)
    
    class Meta:
        model = CompoundFormula
        fields = [
            'id', 'compound_medicine', 'compound_medicine_name',
            'ingredient_medicine', 'ingredient_medicine_name',
            'ratio', 'notes'
        ]

"""
Inventory module admin configuration.
"""

from django.contrib import admin
from .models import (
    MedicineCategory, Supplier, Medicine, Inventory,
    InventoryTransaction, PurchaseOrder, PurchaseOrderItem, CompoundFormula
)


@admin.register(MedicineCategory)
class MedicineCategoryAdmin(admin.ModelAdmin):
    """藥品分類管理"""
    
    list_display = ['code', 'name', 'parent']
    search_fields = ['code', 'name']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """供應商管理"""
    
    list_display = ['code', 'name', 'contact_person', 'phone', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    """藥品管理"""
    
    list_display = ['code', 'name', 'medicine_type', 'category', 'selling_price', 'is_active']
    list_filter = ['medicine_type', 'category', 'is_active']
    search_fields = ['code', 'name', 'pinyin']
    ordering = ['code']
    
    fieldsets = (
        ('基本資料', {
            'fields': ('code', 'name', 'english_name', 'pinyin', 'medicine_type', 'category')
        }),
        ('規格', {
            'fields': ('specification', 'unit', 'package_unit', 'package_quantity')
        }),
        ('供應商', {
            'fields': ('brand', 'supplier', 'external_sku')
        }),
        ('價格', {
            'fields': ('cost_price', 'selling_price', 'safety_stock')
        }),
        ('藥理資訊', {
            'fields': ('properties', 'meridians', 'functions', 'indications', 'contraindications', 'dosage_guide'),
            'classes': ('collapse',)
        }),
        ('其他', {
            'fields': ('notes', 'is_active')
        }),
    )


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    """庫存管理"""
    
    list_display = ['medicine', 'quantity', 'last_updated']
    search_fields = ['medicine__code', 'medicine__name']


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    """庫存異動管理"""
    
    list_display = ['medicine', 'transaction_type', 'quantity', 'before_quantity', 'after_quantity', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['medicine__name', 'reference_number']
    readonly_fields = ['medicine', 'transaction_type', 'quantity', 'before_quantity', 'after_quantity', 'created_at', 'created_by']


class PurchaseOrderItemInline(admin.TabularInline):
    """進貨單項目內聯"""
    model = PurchaseOrderItem
    extra = 0


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    """進貨單管理"""
    
    list_display = ['order_number', 'supplier', 'status', 'order_date', 'total_amount']
    list_filter = ['status', 'supplier', 'order_date']
    search_fields = ['order_number']
    readonly_fields = ['order_number', 'created_at']
    inlines = [PurchaseOrderItemInline]


@admin.register(CompoundFormula)
class CompoundFormulaAdmin(admin.ModelAdmin):
    """複方成份管理"""
    
    list_display = ['compound_medicine', 'ingredient_medicine', 'ratio']
    list_filter = ['compound_medicine']
    search_fields = ['compound_medicine__name', 'ingredient_medicine__name']

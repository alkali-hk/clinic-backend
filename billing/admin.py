"""
Billing module admin configuration.
"""

from django.contrib import admin
from .models import (
    ChargeItem, Bill, BillItem, Payment, Debt,
    ExternalPharmacy, DispensingOrder
)


@admin.register(ChargeItem)
class ChargeItemAdmin(admin.ModelAdmin):
    """收費項目管理"""
    
    list_display = ['code', 'name', 'item_type', 'default_price', 'is_active']
    list_filter = ['item_type', 'is_active']
    search_fields = ['code', 'name']


class BillItemInline(admin.TabularInline):
    """帳單項目內聯"""
    model = BillItem
    extra = 0


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    """帳單管理"""
    
    list_display = ['bill_number', 'patient', 'bill_date', 'total_amount', 'paid_amount', 'status']
    list_filter = ['status', 'bill_date', 'payment_method']
    search_fields = ['bill_number', 'patient__name', 'patient__chart_number']
    readonly_fields = ['bill_number', 'created_at', 'updated_at']
    inlines = [BillItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """付款記錄管理"""
    
    list_display = ['bill', 'amount', 'payment_method', 'created_at', 'created_by']
    list_filter = ['payment_method', 'created_at']
    search_fields = ['bill__bill_number']
    readonly_fields = ['created_at']


@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    """欠款管理"""
    
    list_display = ['patient', 'bill', 'original_amount', 'remaining_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['patient__name', 'patient__chart_number']


@admin.register(ExternalPharmacy)
class ExternalPharmacyAdmin(admin.ModelAdmin):
    """外部配藥房管理"""
    
    list_display = ['name', 'pharmacy_type', 'phone', 'processing_fee', 'delivery_fee', 'is_active']
    list_filter = ['pharmacy_type', 'is_active']
    search_fields = ['name']


@admin.register(DispensingOrder)
class DispensingOrderAdmin(admin.ModelAdmin):
    """派藥訂單管理"""
    
    list_display = ['order_number', 'prescription', 'external_pharmacy', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'external_pharmacy', 'created_at']
    search_fields = ['order_number', 'client_order_id', 'tracking_number']
    readonly_fields = ['order_number', 'client_order_id', 'created_at', 'updated_at']

"""
Billing module serializers.
"""

from rest_framework import serializers
from .models import (
    ChargeItem, Bill, BillItem, Payment, Debt,
    ExternalPharmacy, DispensingOrder
)


class ChargeItemSerializer(serializers.ModelSerializer):
    """收費項目序列化器"""
    
    item_type_display = serializers.CharField(source='get_item_type_display', read_only=True)
    
    class Meta:
        model = ChargeItem
        fields = [
            'id', 'code', 'name', 'item_type', 'item_type_display',
            'default_price', 'is_active', 'notes'
        ]


class BillItemSerializer(serializers.ModelSerializer):
    """帳單項目序列化器"""
    
    class Meta:
        model = BillItem
        fields = [
            'id', 'charge_item', 'prescription', 'description',
            'quantity', 'unit_price', 'subtotal'
        ]


class BillSerializer(serializers.ModelSerializer):
    """帳單序列化器"""
    
    items = BillItemSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_chart_number = serializers.CharField(source='patient.chart_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = Bill
        fields = [
            'id', 'bill_number', 'registration', 'patient', 'patient_name', 'patient_chart_number',
            'bill_date', 'status', 'status_display',
            'subtotal', 'discount', 'total_amount', 'paid_amount', 'balance_due',
            'payment_method', 'payment_method_display', 'paid_at',
            'notes', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'bill_number', 'created_at', 'updated_at']


class BillCreateSerializer(serializers.ModelSerializer):
    """帳單建立序列化器"""
    
    items = BillItemSerializer(many=True)
    
    class Meta:
        model = Bill
        fields = [
            'registration', 'patient', 'bill_date', 'discount', 'notes', 'items'
        ]
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        bill = Bill.objects.create(**validated_data)
        
        subtotal = 0
        for item_data in items_data:
            item = BillItem.objects.create(bill=bill, **item_data)
            subtotal += item.subtotal
        
        bill.subtotal = subtotal
        bill.total_amount = subtotal - bill.discount
        bill.balance_due = bill.total_amount
        bill.save()
        
        return bill


class PaymentSerializer(serializers.ModelSerializer):
    """付款記錄序列化器"""
    
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'bill', 'amount', 'payment_method', 'payment_method_display',
            'reference_number', 'notes', 'created_at', 'created_by', 'created_by_name'
        ]
        read_only_fields = ['id', 'created_at']


class DebtSerializer(serializers.ModelSerializer):
    """欠款記錄序列化器"""
    
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_chart_number = serializers.CharField(source='patient.chart_number', read_only=True)
    bill_number = serializers.CharField(source='bill.bill_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Debt
        fields = [
            'id', 'patient', 'patient_name', 'patient_chart_number',
            'bill', 'bill_number',
            'original_amount', 'remaining_amount',
            'status', 'status_display', 'due_date', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExternalPharmacySerializer(serializers.ModelSerializer):
    """外部配藥房序列化器"""
    
    pharmacy_type_display = serializers.CharField(source='get_pharmacy_type_display', read_only=True)
    
    class Meta:
        model = ExternalPharmacy
        fields = [
            'id', 'name', 'pharmacy_type', 'pharmacy_type_display',
            'contact_person', 'phone', 'email', 'address',
            'processing_fee', 'delivery_fee',
            'api_endpoint', 'api_key', 'webhook_api_key', 'api_request_format',
            'is_active', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'api_key': {'write_only': True},
            'webhook_api_key': {'write_only': True}
        }


class DispensingOrderSerializer(serializers.ModelSerializer):
    """派藥訂單序列化器"""
    
    prescription_number = serializers.CharField(source='prescription.prescription_number', read_only=True)
    external_pharmacy_name = serializers.CharField(source='external_pharmacy.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DispensingOrder
        fields = [
            'id', 'order_number', 'client_order_id',
            'prescription', 'prescription_number',
            'external_pharmacy', 'external_pharmacy_name',
            'status', 'status_display',
            'medicine_fee', 'processing_fee', 'delivery_fee', 'total_amount',
            'recipient_name', 'recipient_phone', 'recipient_address',
            'tracking_company', 'tracking_number',
            'api_response', 'error_message',
            'notes', 'sent_at', 'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'order_number', 'client_order_id',
            'api_response', 'error_message',
            'sent_at', 'completed_at', 'created_at', 'updated_at'
        ]


class DispensingOrderCreateSerializer(serializers.ModelSerializer):
    """派藥訂單建立序列化器"""
    
    class Meta:
        model = DispensingOrder
        fields = [
            'prescription', 'external_pharmacy',
            'medicine_fee', 'processing_fee', 'delivery_fee',
            'recipient_name', 'recipient_phone', 'recipient_address', 'notes'
        ]

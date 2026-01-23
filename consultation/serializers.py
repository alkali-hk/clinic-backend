"""
Consultation module serializers.
"""

from rest_framework import serializers
from .models import (
    DiagnosticTerm, Consultation, Prescription, PrescriptionItem,
    ExperienceFormula, ExperienceFormulaItem, Certificate
)


class DiagnosticTermSerializer(serializers.ModelSerializer):
    """辨證詞庫序列化器"""
    
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = DiagnosticTerm
        fields = ['id', 'category', 'category_display', 'code', 'name', 'description', 'is_active']


class PrescriptionItemSerializer(serializers.ModelSerializer):
    """處方項目序列化器"""
    
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    medicine_code = serializers.CharField(source='medicine.code', read_only=True)
    
    class Meta:
        model = PrescriptionItem
        fields = [
            'id', 'medicine', 'medicine_name', 'medicine_code',
            'dosage', 'unit', 'decoction_method',
            'unit_price', 'subtotal', 'notes'
        ]


class PrescriptionSerializer(serializers.ModelSerializer):
    """處方序列化器"""
    
    items = PrescriptionItemSerializer(many=True, read_only=True)
    dispensing_method_display = serializers.CharField(source='get_dispensing_method_display', read_only=True)
    external_pharmacy_name = serializers.CharField(source='external_pharmacy.name', read_only=True)
    
    class Meta:
        model = Prescription
        fields = [
            'id', 'consultation', 'prescription_number', 'name',
            'total_doses', 'doses_per_day', 'days', 'usage_instruction',
            'dispensing_method', 'dispensing_method_display',
            'external_pharmacy', 'external_pharmacy_name',
            'medicine_fee', 'is_dispensed', 'dispensed_at',
            'notes', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'prescription_number', 'created_at', 'updated_at']


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    """處方建立序列化器"""
    
    items = PrescriptionItemSerializer(many=True)
    
    class Meta:
        model = Prescription
        fields = [
            'consultation', 'name', 'total_doses', 'doses_per_day', 'days',
            'usage_instruction', 'dispensing_method', 'external_pharmacy',
            'notes', 'items'
        ]
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        prescription = Prescription.objects.create(**validated_data)
        
        total_fee = 0
        for item_data in items_data:
            item = PrescriptionItem.objects.create(prescription=prescription, **item_data)
            total_fee += item.subtotal
        
        prescription.medicine_fee = total_fee
        prescription.save()
        
        return prescription
    
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        
        # 更新處方基本資料
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # 更新處方項目
        if items_data is not None:
            instance.items.all().delete()
            total_fee = 0
            for item_data in items_data:
                item = PrescriptionItem.objects.create(prescription=instance, **item_data)
                total_fee += item.subtotal
            instance.medicine_fee = total_fee
        
        instance.save()
        return instance


class ConsultationSerializer(serializers.ModelSerializer):
    """診療記錄序列化器"""
    
    patient_name = serializers.CharField(source='registration.patient.name', read_only=True)
    patient_chart_number = serializers.CharField(source='registration.patient.chart_number', read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    prescriptions = PrescriptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Consultation
        fields = [
            'id', 'registration', 'doctor', 'doctor_name',
            'patient_name', 'patient_chart_number',
            'chief_complaint', 'present_illness', 'past_history',
            'inspection', 'tongue_appearance', 'listening_smelling',
            'inquiry', 'pulse', 'palpation',
            'tcm_diagnosis', 'western_diagnosis', 'syndrome_differentiation', 'treatment_principle',
            'advice', 'follow_up_date', 'notes',
            'prescriptions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'doctor', 'created_at', 'updated_at']


class ConsultationListSerializer(serializers.ModelSerializer):
    """診療記錄列表序列化器"""
    
    patient_name = serializers.CharField(source='registration.patient.name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    
    class Meta:
        model = Consultation
        fields = [
            'id', 'registration', 'doctor', 'doctor_name',
            'patient_name', 'tcm_diagnosis', 'created_at'
        ]


class ExperienceFormulaItemSerializer(serializers.ModelSerializer):
    """經驗方項目序列化器"""
    
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    medicine_code = serializers.CharField(source='medicine.code', read_only=True)
    
    class Meta:
        model = ExperienceFormulaItem
        fields = [
            'id', 'medicine', 'medicine_name', 'medicine_code',
            'dosage', 'unit', 'decoction_method', 'notes'
        ]


class ExperienceFormulaSerializer(serializers.ModelSerializer):
    """經驗方序列化器"""
    
    items = ExperienceFormulaItemSerializer(many=True, read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    
    class Meta:
        model = ExperienceFormula
        fields = [
            'id', 'doctor', 'doctor_name', 'name', 'category',
            'indication', 'usage_instruction', 'notes', 'is_public',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExperienceFormulaCreateSerializer(serializers.ModelSerializer):
    """經驗方建立序列化器"""
    
    items = ExperienceFormulaItemSerializer(many=True)
    
    class Meta:
        model = ExperienceFormula
        fields = [
            'name', 'category', 'indication', 'usage_instruction',
            'notes', 'is_public', 'items'
        ]
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        formula = ExperienceFormula.objects.create(**validated_data)
        
        for item_data in items_data:
            ExperienceFormulaItem.objects.create(formula=formula, **item_data)
        
        return formula


class CertificateSerializer(serializers.ModelSerializer):
    """證明書序列化器"""
    
    certificate_type_display = serializers.CharField(source='get_certificate_type_display', read_only=True)
    patient_name = serializers.CharField(source='consultation.registration.patient.name', read_only=True)
    
    class Meta:
        model = Certificate
        fields = [
            'id', 'consultation', 'certificate_type', 'certificate_type_display',
            'certificate_number', 'content', 'issue_date',
            'sick_leave_start', 'sick_leave_end',
            'print_count', 'last_printed_at',
            'patient_name', 'created_at', 'created_by'
        ]
        read_only_fields = ['id', 'certificate_number', 'print_count', 'last_printed_at', 'created_at']

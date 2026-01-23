"""
Patients module serializers.
"""

from rest_framework import serializers
from .models import Patient, PatientImage


class PatientImageSerializer(serializers.ModelSerializer):
    """病患影像序列化器"""
    
    image_type_display = serializers.CharField(source='get_image_type_display', read_only=True)
    
    class Meta:
        model = PatientImage
        fields = [
            'id', 'patient', 'image_type', 'image_type_display',
            'image', 'description', 'taken_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PatientSerializer(serializers.ModelSerializer):
    """病患序列化器"""
    
    age = serializers.IntegerField(read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    masked_id_card = serializers.SerializerMethodField()
    masked_phone = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = [
            'id', 'chart_number', 'name', 'gender', 'gender_display',
            'birth_date', 'age', 'id_card_number', 'masked_id_card',
            'phone', 'masked_phone', 'mobile', 'address', 'email',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation',
            'blood_type', 'allergies', 'medical_history', 'notes',
            'balance', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'chart_number', 'created_at', 'updated_at']
    
    def get_masked_id_card(self, obj):
        # 根據使用者設定決定是否遮罩
        request = self.context.get('request')
        if request and hasattr(request.user, 'data_masking_enabled'):
            if request.user.data_masking_enabled:
                return obj.get_masked_id_card()
        return obj.id_card_number
    
    def get_masked_phone(self, obj):
        request = self.context.get('request')
        if request and hasattr(request.user, 'data_masking_enabled'):
            if request.user.data_masking_enabled:
                return obj.get_masked_phone()
        return obj.phone


class PatientListSerializer(serializers.ModelSerializer):
    """病患列表序列化器（簡化版）"""
    
    age = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Patient
        fields = [
            'id', 'chart_number', 'name', 'gender', 'birth_date', 'age',
            'phone', 'is_active'
        ]

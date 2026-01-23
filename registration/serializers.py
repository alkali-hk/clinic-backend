"""
Registration module serializers.
"""

from rest_framework import serializers
from .models import Appointment, Registration


class AppointmentSerializer(serializers.ModelSerializer):
    """預約序列化器"""
    
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_chart_number = serializers.CharField(source='patient.chart_number', read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'patient_name', 'patient_chart_number',
            'doctor', 'doctor_name', 'room', 'room_name',
            'appointment_date', 'appointment_time',
            'status', 'status_display', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RegistrationSerializer(serializers.ModelSerializer):
    """掛號序列化器"""
    
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_chart_number = serializers.CharField(source='patient.chart_number', read_only=True)
    patient_phone = serializers.CharField(source='patient.phone', read_only=True)
    patient_allergies = serializers.CharField(source='patient.allergies', read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    visit_type_display = serializers.CharField(source='get_visit_type_display', read_only=True)
    
    class Meta:
        model = Registration
        fields = [
            'id', 'registration_number', 'queue_number',
            'patient', 'patient_name', 'patient_chart_number', 'patient_phone', 'patient_allergies',
            'doctor', 'doctor_name', 'room', 'room_name',
            'appointment', 'visit_type', 'visit_type_display',
            'status', 'status_display',
            'registration_date', 'registration_time',
            'check_in_time', 'consultation_start_time', 'consultation_end_time',
            'registration_fee', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'registration_number', 'created_at', 'updated_at']


class RegistrationCreateSerializer(serializers.ModelSerializer):
    """掛號建立序列化器"""
    
    class Meta:
        model = Registration
        fields = [
            'patient', 'doctor', 'room', 'appointment',
            'visit_type', 'registration_date', 'registration_fee', 'notes'
        ]
    
    def create(self, validated_data):
        # 計算當日該醫師的候診號碼
        from datetime import date
        reg_date = validated_data.get('registration_date', date.today())
        doctor = validated_data.get('doctor')
        
        last_queue = Registration.objects.filter(
            registration_date=reg_date,
            doctor=doctor
        ).order_by('-queue_number').first()
        
        queue_number = (last_queue.queue_number + 1) if last_queue else 1
        validated_data['queue_number'] = queue_number
        
        return super().create(validated_data)


class QueueItemSerializer(serializers.ModelSerializer):
    """候診列表項目序列化器"""
    
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_chart_number = serializers.CharField(source='patient.chart_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    visit_type_display = serializers.CharField(source='get_visit_type_display', read_only=True)
    
    class Meta:
        model = Registration
        fields = [
            'id', 'registration_number', 'queue_number',
            'patient', 'patient_name', 'patient_chart_number',
            'visit_type', 'visit_type_display',
            'status', 'status_display',
            'check_in_time'
        ]

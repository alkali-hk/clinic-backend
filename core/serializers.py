"""
Core module serializers.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ClinicSettings, ClinicRoom, Schedule

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """使用者序列化器"""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'phone', 'certificate_number',
            'data_masking_enabled', 'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserCreateSerializer(serializers.ModelSerializer):
    """使用者建立序列化器"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'password', 'email', 'first_name', 'last_name',
            'role', 'phone', 'certificate_number'
        ]
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ClinicSettingsSerializer(serializers.ModelSerializer):
    """診所設定序列化器"""
    
    class Meta:
        model = ClinicSettings
        fields = '__all__'


class ClinicRoomSerializer(serializers.ModelSerializer):
    """診間序列化器"""
    
    class Meta:
        model = ClinicRoom
        fields = '__all__'


class ScheduleSerializer(serializers.ModelSerializer):
    """排班序列化器"""
    
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    period_display = serializers.CharField(source='get_period_display', read_only=True)
    
    class Meta:
        model = Schedule
        fields = [
            'id', 'doctor', 'doctor_name', 'room', 'room_name',
            'day_of_week', 'day_of_week_display', 'period', 'period_display',
            'start_time', 'end_time', 'max_patients', 'is_active'
        ]

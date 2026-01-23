"""
Patients module admin configuration.
"""

from django.contrib import admin
from .models import Patient, PatientImage


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """病患管理"""
    
    list_display = ['chart_number', 'name', 'gender', 'birth_date', 'phone', 'is_active', 'created_at']
    list_filter = ['gender', 'is_active', 'created_at']
    search_fields = ['chart_number', 'name', 'phone', 'id_card_number']
    ordering = ['-created_at']
    readonly_fields = ['chart_number', 'created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('基本資料', {
            'fields': ('chart_number', 'name', 'gender', 'birth_date', 'id_card_number')
        }),
        ('聯絡資料', {
            'fields': ('phone', 'mobile', 'address', 'email')
        }),
        ('緊急聯絡人', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation')
        }),
        ('醫療資訊', {
            'fields': ('blood_type', 'allergies', 'medical_history', 'notes')
        }),
        ('帳戶資訊', {
            'fields': ('balance',)
        }),
        ('系統資訊', {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PatientImage)
class PatientImageAdmin(admin.ModelAdmin):
    """病患影像管理"""
    
    list_display = ['patient', 'image_type', 'created_at', 'created_by']
    list_filter = ['image_type', 'created_at']
    search_fields = ['patient__name', 'patient__chart_number']

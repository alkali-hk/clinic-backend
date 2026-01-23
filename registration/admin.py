"""
Registration module admin configuration.
"""

from django.contrib import admin
from .models import Appointment, Registration


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """預約管理"""
    
    list_display = ['patient', 'doctor', 'appointment_date', 'appointment_time', 'status', 'created_at']
    list_filter = ['status', 'doctor', 'appointment_date']
    search_fields = ['patient__name', 'patient__chart_number']
    ordering = ['-appointment_date', '-appointment_time']
    date_hierarchy = 'appointment_date'


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    """掛號管理"""
    
    list_display = ['registration_number', 'patient', 'doctor', 'queue_number', 'visit_type', 'status', 'registration_date']
    list_filter = ['status', 'visit_type', 'doctor', 'registration_date']
    search_fields = ['registration_number', 'patient__name', 'patient__chart_number']
    ordering = ['-registration_date', 'queue_number']
    date_hierarchy = 'registration_date'
    readonly_fields = ['registration_number', 'created_at', 'updated_at']

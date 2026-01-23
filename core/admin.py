"""
Core module admin configuration.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, ClinicSettings, ClinicRoom, Schedule, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """自定義使用者管理"""
    
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering = ['username']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        (_('診所資訊'), {'fields': ('role', 'phone', 'certificate_number', 'data_masking_enabled')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('診所資訊'), {'fields': ('role', 'phone', 'certificate_number')}),
    )


@admin.register(ClinicSettings)
class ClinicSettingsAdmin(admin.ModelAdmin):
    """診所設定管理"""
    
    list_display = ['clinic_name', 'phone', 'enable_data_masking', 'updated_at']


@admin.register(ClinicRoom)
class ClinicRoomAdmin(admin.ModelAdmin):
    """診間管理"""
    
    list_display = ['code', 'name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    """排班管理"""
    
    list_display = ['doctor', 'room', 'day_of_week', 'period', 'start_time', 'end_time', 'is_active']
    list_filter = ['doctor', 'room', 'day_of_week', 'period', 'is_active']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """稽核日誌管理"""
    
    list_display = ['user', 'action', 'model_name', 'object_id', 'created_at']
    list_filter = ['action', 'model_name', 'created_at']
    search_fields = ['user__username', 'model_name', 'object_id']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'before_data', 'after_data', 'ip_address', 'user_agent', 'created_at']

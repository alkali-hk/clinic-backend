"""
Consultation module admin configuration.
"""

from django.contrib import admin
from .models import (
    DiagnosticTerm, Consultation, Prescription, PrescriptionItem,
    ExperienceFormula, ExperienceFormulaItem, Certificate
)


@admin.register(DiagnosticTerm)
class DiagnosticTermAdmin(admin.ModelAdmin):
    """辨證詞庫管理"""
    
    list_display = ['category', 'code', 'name', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['code', 'name']
    ordering = ['category', 'name']


class PrescriptionItemInline(admin.TabularInline):
    """處方項目內聯"""
    model = PrescriptionItem
    extra = 0
    readonly_fields = ['subtotal']


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    """處方管理"""
    
    list_display = ['prescription_number', 'consultation', 'dispensing_method', 'medicine_fee', 'is_dispensed', 'created_at']
    list_filter = ['dispensing_method', 'is_dispensed', 'created_at']
    search_fields = ['prescription_number', 'consultation__registration__patient__name']
    readonly_fields = ['prescription_number', 'created_at', 'updated_at']
    inlines = [PrescriptionItemInline]


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    """診療記錄管理"""
    
    list_display = ['registration', 'doctor', 'tcm_diagnosis', 'created_at']
    list_filter = ['doctor', 'created_at']
    search_fields = ['registration__patient__name', 'tcm_diagnosis']
    readonly_fields = ['created_at', 'updated_at']


class ExperienceFormulaItemInline(admin.TabularInline):
    """經驗方項目內聯"""
    model = ExperienceFormulaItem
    extra = 0


@admin.register(ExperienceFormula)
class ExperienceFormulaAdmin(admin.ModelAdmin):
    """經驗方管理"""
    
    list_display = ['name', 'doctor', 'category', 'is_public', 'created_at']
    list_filter = ['doctor', 'category', 'is_public']
    search_fields = ['name', 'indication']
    inlines = [ExperienceFormulaItemInline]


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """證明書管理"""
    
    list_display = ['certificate_number', 'certificate_type', 'consultation', 'issue_date', 'print_count']
    list_filter = ['certificate_type', 'issue_date']
    search_fields = ['certificate_number', 'consultation__registration__patient__name']
    readonly_fields = ['certificate_number', 'print_count', 'last_printed_at', 'created_at']

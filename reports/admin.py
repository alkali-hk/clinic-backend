"""
Reports module admin configuration.
"""

from django.contrib import admin
from .models import ReportTemplate, GeneratedReport


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    """報表範本管理"""
    
    list_display = ['name', 'report_type', 'is_active', 'created_at']
    list_filter = ['report_type', 'is_active']
    search_fields = ['name']


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    """已生成報表管理"""
    
    list_display = ['name', 'template', 'generated_at', 'generated_by']
    list_filter = ['template', 'generated_at']
    search_fields = ['name']
    readonly_fields = ['generated_at']

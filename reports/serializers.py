"""
Reports module serializers.
"""

from rest_framework import serializers
from .models import ReportTemplate, GeneratedReport


class ReportTemplateSerializer(serializers.ModelSerializer):
    """報表範本序列化器"""
    
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    
    class Meta:
        model = ReportTemplate
        fields = [
            'id', 'name', 'report_type', 'report_type_display',
            'description', 'query_template', 'is_active', 'created_at'
        ]


class GeneratedReportSerializer(serializers.ModelSerializer):
    """已生成報表序列化器"""
    
    template_name = serializers.CharField(source='template.name', read_only=True)
    generated_by_name = serializers.CharField(source='generated_by.get_full_name', read_only=True)
    
    class Meta:
        model = GeneratedReport
        fields = [
            'id', 'template', 'template_name', 'name',
            'parameters', 'result_data', 'file',
            'generated_at', 'generated_by', 'generated_by_name'
        ]

"""
Reports models for Clinic Management System.
報表模組 - 報表相關模型
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class ReportTemplate(models.Model):
    """
    報表範本
    """
    
    class ReportType(models.TextChoices):
        DAILY_SUMMARY = 'daily_summary', _('每日結算報表')
        MONTHLY_SUMMARY = 'monthly_summary', _('月結報表')
        DOCTOR_WORKLOAD = 'doctor_workload', _('醫師工作量統計')
        MEDICINE_USAGE = 'medicine_usage', _('藥品使用統計')
        PATIENT_VISIT = 'patient_visit', _('病患就診統計')
        REVENUE = 'revenue', _('營收報表')
        INVENTORY = 'inventory', _('庫存報表')
        EXTERNAL_PHARMACY = 'external_pharmacy', _('外部配藥房對帳')
        CUSTOM = 'custom', _('自訂報表')
    
    name = models.CharField(
        max_length=100,
        verbose_name=_('報表名稱')
    )
    report_type = models.CharField(
        max_length=30,
        choices=ReportType.choices,
        verbose_name=_('報表類型')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('描述')
    )
    query_template = models.TextField(
        blank=True,
        verbose_name=_('查詢範本')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('是否啟用')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('建立時間')
    )
    
    class Meta:
        verbose_name = _('報表範本')
        verbose_name_plural = _('報表範本')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class GeneratedReport(models.Model):
    """
    已生成報表
    """
    
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports',
        verbose_name=_('報表範本')
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_('報表名稱')
    )
    parameters = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('查詢參數')
    )
    result_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('報表資料')
    )
    file = models.FileField(
        upload_to='reports/%Y/%m/',
        null=True,
        blank=True,
        verbose_name=_('報表檔案')
    )
    generated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('生成時間')
    )
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports',
        verbose_name=_('生成者')
    )
    
    class Meta:
        verbose_name = _('已生成報表')
        verbose_name_plural = _('已生成報表')
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.name} - {self.generated_at.date()}"

"""
Core models for Clinic Management System.
核心模組 - 使用者、診所設定等基礎模型
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    自定義使用者模型
    擴展 Django 內建的 User 模型，增加診所系統所需的欄位
    """
    
    class Role(models.TextChoices):
        ADMIN = 'admin', _('系統管理員')
        DOCTOR = 'doctor', _('醫師')
        ASSISTANT = 'assistant', _('助理')
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ASSISTANT,
        verbose_name=_('角色')
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('聯絡電話')
    )
    certificate_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('醫師證書號碼')
    )
    data_masking_enabled = models.BooleanField(
        default=False,
        verbose_name=_('啟用資料遮罩')
    )
    
    class Meta:
        verbose_name = _('使用者')
        verbose_name_plural = _('使用者')
        ordering = ['username']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    @property
    def is_doctor(self):
        return self.role == self.Role.DOCTOR
    
    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN


class ClinicSettings(models.Model):
    """
    診所設定
    儲存診所的基本資訊和系統設定
    """
    
    clinic_name = models.CharField(
        max_length=100,
        verbose_name=_('診所名稱')
    )
    address = models.TextField(
        blank=True,
        verbose_name=_('地址')
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('電話')
    )
    fax = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('傳真')
    )
    email = models.EmailField(
        blank=True,
        verbose_name=_('電子郵件')
    )
    logo = models.ImageField(
        upload_to='clinic/',
        blank=True,
        null=True,
        verbose_name=_('診所標誌')
    )
    
    # 系統設定
    enable_data_masking = models.BooleanField(
        default=False,
        verbose_name=_('啟用資料遮罩')
    )
    appointment_slot_duration = models.PositiveIntegerField(
        default=15,
        verbose_name=_('預約時段長度（分鐘）')
    )
    auto_queue_mode = models.CharField(
        max_length=20,
        choices=[
            ('auto_front', '自動排前'),
            ('manual', '助理手動調整'),
            ('doctor_choice', '醫師自由選擇'),
        ],
        default='manual',
        verbose_name=_('過號處理模式')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('診所設定')
        verbose_name_plural = _('診所設定')
    
    def __str__(self):
        return self.clinic_name


class ClinicRoom(models.Model):
    """
    診間
    """
    
    name = models.CharField(
        max_length=50,
        verbose_name=_('診間名稱')
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_('診間代碼')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('是否啟用')
    )
    
    class Meta:
        verbose_name = _('診間')
        verbose_name_plural = _('診間')
        ordering = ['code']
    
    def __str__(self):
        return self.name


class Schedule(models.Model):
    """
    醫師排班
    """
    
    class DayOfWeek(models.IntegerChoices):
        SUNDAY = 0, _('星期日')
        MONDAY = 1, _('星期一')
        TUESDAY = 2, _('星期二')
        WEDNESDAY = 3, _('星期三')
        THURSDAY = 4, _('星期四')
        FRIDAY = 5, _('星期五')
        SATURDAY = 6, _('星期六')
    
    class Period(models.TextChoices):
        MORNING = 'morning', _('上午')
        AFTERNOON = 'afternoon', _('下午')
        EVENING = 'evening', _('晚間')
    
    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'doctor'},
        related_name='schedules',
        verbose_name=_('醫師')
    )
    room = models.ForeignKey(
        ClinicRoom,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name=_('診間')
    )
    day_of_week = models.IntegerField(
        choices=DayOfWeek.choices,
        verbose_name=_('星期')
    )
    period = models.CharField(
        max_length=20,
        choices=Period.choices,
        verbose_name=_('時段')
    )
    start_time = models.TimeField(
        verbose_name=_('開始時間')
    )
    end_time = models.TimeField(
        verbose_name=_('結束時間')
    )
    max_patients = models.PositiveIntegerField(
        default=30,
        verbose_name=_('最大看診人數')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('是否啟用')
    )
    
    class Meta:
        verbose_name = _('排班')
        verbose_name_plural = _('排班')
        unique_together = ['doctor', 'day_of_week', 'period']
        ordering = ['day_of_week', 'period']
    
    def __str__(self):
        return f"{self.doctor.get_full_name()} - {self.get_day_of_week_display()} {self.get_period_display()}"


class AuditLog(models.Model):
    """
    稽核日誌
    記錄所有敏感操作的詳細日誌
    """
    
    class Action(models.TextChoices):
        CREATE = 'create', _('新增')
        UPDATE = 'update', _('修改')
        DELETE = 'delete', _('刪除')
        VIEW = 'view', _('查看')
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name=_('操作人員')
    )
    action = models.CharField(
        max_length=20,
        choices=Action.choices,
        verbose_name=_('操作類型')
    )
    model_name = models.CharField(
        max_length=100,
        verbose_name=_('模型名稱')
    )
    object_id = models.CharField(
        max_length=100,
        verbose_name=_('物件 ID')
    )
    before_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('修改前資料')
    )
    after_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('修改後資料')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP 位址')
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User Agent')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('操作時間')
    )
    
    class Meta:
        verbose_name = _('稽核日誌')
        verbose_name_plural = _('稽核日誌')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.get_action_display()} {self.model_name}"

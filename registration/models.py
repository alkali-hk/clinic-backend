"""
Registration models for Clinic Management System.
掛號模組 - 掛號與預約管理
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Appointment(models.Model):
    """
    預約
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('待確認')
        CONFIRMED = 'confirmed', _('已確認')
        CANCELLED = 'cancelled', _('已取消')
        COMPLETED = 'completed', _('已完成')
    
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name=_('病患')
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'doctor'},
        related_name='appointments',
        verbose_name=_('醫師')
    )
    room = models.ForeignKey(
        'core.ClinicRoom',
        on_delete=models.SET_NULL,
        null=True,
        related_name='appointments',
        verbose_name=_('診間')
    )
    appointment_date = models.DateField(
        verbose_name=_('預約日期')
    )
    appointment_time = models.TimeField(
        verbose_name=_('預約時間')
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_('狀態')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('備註')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('建立時間')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('更新時間')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_appointments',
        verbose_name=_('建立者')
    )
    
    class Meta:
        verbose_name = _('預約')
        verbose_name_plural = _('預約')
        ordering = ['appointment_date', 'appointment_time']
        indexes = [
            models.Index(fields=['appointment_date', 'doctor']),
            models.Index(fields=['patient', 'appointment_date']),
        ]
    
    def __str__(self):
        return f"{self.patient.name} - {self.appointment_date} {self.appointment_time}"


class Registration(models.Model):
    """
    掛號
    """
    
    class Status(models.TextChoices):
        WAITING = 'waiting', _('候診中')
        IN_CONSULTATION = 'in_consultation', _('看診中')
        COMPLETED = 'completed', _('已完成')
        CANCELLED = 'cancelled', _('已取消')
        NO_SHOW = 'no_show', _('過號')
    
    class VisitType(models.TextChoices):
        FIRST_VISIT = 'first_visit', _('初診')
        FOLLOW_UP = 'follow_up', _('覆診')
    
    # 關聯
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name='registrations',
        verbose_name=_('病患')
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'doctor'},
        related_name='registrations',
        verbose_name=_('醫師')
    )
    room = models.ForeignKey(
        'core.ClinicRoom',
        on_delete=models.SET_NULL,
        null=True,
        related_name='registrations',
        verbose_name=_('診間')
    )
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registration',
        verbose_name=_('關聯預約')
    )
    
    # 掛號資訊
    registration_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('掛號號碼')
    )
    queue_number = models.PositiveIntegerField(
        verbose_name=_('候診號碼')
    )
    visit_type = models.CharField(
        max_length=20,
        choices=VisitType.choices,
        default=VisitType.FOLLOW_UP,
        verbose_name=_('就診類型')
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING,
        verbose_name=_('狀態')
    )
    
    # 時間記錄
    registration_date = models.DateField(
        verbose_name=_('掛號日期')
    )
    registration_time = models.TimeField(
        auto_now_add=True,
        verbose_name=_('掛號時間')
    )
    check_in_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('報到時間')
    )
    consultation_start_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('看診開始時間')
    )
    consultation_end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('看診結束時間')
    )
    
    # 費用
    registration_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('掛號費')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('備註')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('建立時間')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('更新時間')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_registrations',
        verbose_name=_('建立者')
    )
    
    class Meta:
        verbose_name = _('掛號')
        verbose_name_plural = _('掛號')
        ordering = ['registration_date', 'queue_number']
        indexes = [
            models.Index(fields=['registration_date', 'doctor']),
            models.Index(fields=['patient', 'registration_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.registration_number} - {self.patient.name}"
    
    def save(self, *args, **kwargs):
        if not self.registration_number:
            # 自動生成掛號號碼
            from datetime import date
            today = date.today()
            prefix = today.strftime('%Y%m%d')
            last_reg = Registration.objects.filter(
                registration_number__startswith=prefix
            ).order_by('-registration_number').first()
            
            if last_reg:
                last_num = int(last_reg.registration_number[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.registration_number = f"{prefix}{new_num:04d}"
        
        super().save(*args, **kwargs)

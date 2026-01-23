"""
Patient models for Clinic Management System.
病患模組 - 病患資料管理
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Patient(models.Model):
    """
    病患資料
    """
    
    class Gender(models.TextChoices):
        MALE = 'male', _('男')
        FEMALE = 'female', _('女')
        OTHER = 'other', _('其他')
    
    # 基本資料
    chart_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('病歷號碼')
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('姓名')
    )
    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        verbose_name=_('性別')
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('出生日期')
    )
    id_card_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('身份證號碼')
    )
    
    # 聯絡資料
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('電話')
    )
    mobile = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('手機')
    )
    address = models.TextField(
        blank=True,
        verbose_name=_('地址')
    )
    email = models.EmailField(
        blank=True,
        verbose_name=_('電子郵件')
    )
    
    # 緊急聯絡人
    emergency_contact_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('緊急聯絡人姓名')
    )
    emergency_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('緊急聯絡人電話')
    )
    emergency_contact_relation = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('與病患關係')
    )
    
    # 醫療資訊
    blood_type = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_('血型')
    )
    allergies = models.TextField(
        blank=True,
        verbose_name=_('過敏史')
    )
    medical_history = models.TextField(
        blank=True,
        verbose_name=_('病史')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('備註')
    )
    
    # 帳戶資訊
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('帳戶餘額')
    )
    
    # 系統欄位
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('是否有效')
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
        related_name='created_patients',
        verbose_name=_('建立者')
    )
    
    class Meta:
        verbose_name = _('病患')
        verbose_name_plural = _('病患')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['chart_number']),
            models.Index(fields=['name']),
            models.Index(fields=['phone']),
            models.Index(fields=['id_card_number']),
        ]
    
    def __str__(self):
        return f"{self.chart_number} - {self.name}"
    
    @property
    def age(self):
        """計算年齡"""
        if not self.birth_date:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
    
    def get_masked_id_card(self):
        """取得遮罩後的身份證號碼"""
        if len(self.id_card_number) > 6:
            return f"{self.id_card_number[:4]}***{self.id_card_number[-3:]}"
        return self.id_card_number
    
    def get_masked_phone(self):
        """取得遮罩後的電話號碼"""
        if len(self.phone) > 4:
            return f"{self.phone[:4]}****"
        return self.phone


class PatientImage(models.Model):
    """
    病患影像
    用於儲存病患的相關影像資料（如舌診照片等）
    """
    
    class ImageType(models.TextChoices):
        TONGUE = 'tongue', _('舌診')
        FACE = 'face', _('面診')
        OTHER = 'other', _('其他')
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('病患')
    )
    image_type = models.CharField(
        max_length=20,
        choices=ImageType.choices,
        default=ImageType.OTHER,
        verbose_name=_('影像類型')
    )
    image = models.ImageField(
        upload_to='patient_images/%Y/%m/',
        verbose_name=_('影像檔案')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('描述')
    )
    taken_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('拍攝時間')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('上傳時間')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_patient_images',
        verbose_name=_('上傳者')
    )
    
    class Meta:
        verbose_name = _('病患影像')
        verbose_name_plural = _('病患影像')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient.name} - {self.get_image_type_display()}"

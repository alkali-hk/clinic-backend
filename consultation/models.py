"""
Consultation models for Clinic Management System.
診療模組 - 診療記錄與處方管理
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class DiagnosticTerm(models.Model):
    """
    辨證詞庫
    """
    
    class Category(models.TextChoices):
        CHIEF_COMPLAINT = 'chief_complaint', _('主訴')
        SYMPTOM = 'symptom', _('症狀')
        TONGUE = 'tongue', _('舌象')
        PULSE = 'pulse', _('脈象')
        DIAGNOSIS = 'diagnosis', _('診斷')
        TREATMENT = 'treatment', _('治則')
    
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        verbose_name=_('類別')
    )
    code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('代碼')
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('名稱')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('描述')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('是否啟用')
    )
    
    class Meta:
        verbose_name = _('辨證詞庫')
        verbose_name_plural = _('辨證詞庫')
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category', 'name']),
        ]
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.name}"


class Consultation(models.Model):
    """
    診療記錄
    """
    
    registration = models.OneToOneField(
        'registration.Registration',
        on_delete=models.CASCADE,
        related_name='consultation',
        verbose_name=_('掛號')
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'doctor'},
        related_name='consultations',
        verbose_name=_('醫師')
    )
    
    # 四診記錄
    chief_complaint = models.TextField(
        blank=True,
        verbose_name=_('主訴')
    )
    present_illness = models.TextField(
        blank=True,
        verbose_name=_('現病史')
    )
    past_history = models.TextField(
        blank=True,
        verbose_name=_('既往史')
    )
    
    # 望診
    inspection = models.TextField(
        blank=True,
        verbose_name=_('望診')
    )
    tongue_appearance = models.TextField(
        blank=True,
        verbose_name=_('舌象')
    )
    
    # 聞診
    listening_smelling = models.TextField(
        blank=True,
        verbose_name=_('聞診')
    )
    
    # 問診
    inquiry = models.TextField(
        blank=True,
        verbose_name=_('問診')
    )
    
    # 切診
    pulse = models.TextField(
        blank=True,
        verbose_name=_('脈象')
    )
    palpation = models.TextField(
        blank=True,
        verbose_name=_('觸診')
    )
    
    # 診斷
    tcm_diagnosis = models.TextField(
        blank=True,
        verbose_name=_('中醫診斷')
    )
    western_diagnosis = models.TextField(
        blank=True,
        verbose_name=_('西醫診斷')
    )
    syndrome_differentiation = models.TextField(
        blank=True,
        verbose_name=_('辨證')
    )
    treatment_principle = models.TextField(
        blank=True,
        verbose_name=_('治則')
    )
    
    # 醫囑
    advice = models.TextField(
        blank=True,
        verbose_name=_('醫囑')
    )
    follow_up_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('覆診日期')
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
    
    class Meta:
        verbose_name = _('診療記錄')
        verbose_name_plural = _('診療記錄')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.registration.patient.name} - {self.created_at.date()}"


class Prescription(models.Model):
    """
    處方
    """
    
    class DispensingMethod(models.TextChoices):
        INTERNAL = 'internal', _('內部配藥')
        EXTERNAL_DECOCTION = 'external_decoction', _('外送煎藥')
        EXTERNAL_CONCENTRATE = 'external_concentrate', _('外送濃縮')
    
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name='prescriptions',
        verbose_name=_('診療記錄')
    )
    
    # 處方資訊
    prescription_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('處方編號')
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('處方名稱')
    )
    
    # 劑量資訊
    total_doses = models.PositiveIntegerField(
        default=1,
        verbose_name=_('總劑數')
    )
    doses_per_day = models.PositiveIntegerField(
        default=1,
        verbose_name=_('每日劑數')
    )
    days = models.PositiveIntegerField(
        default=1,
        verbose_name=_('天數')
    )
    
    # 服用方式
    usage_instruction = models.TextField(
        blank=True,
        verbose_name=_('服用方法')
    )
    
    # 派藥方式
    dispensing_method = models.CharField(
        max_length=30,
        choices=DispensingMethod.choices,
        default=DispensingMethod.INTERNAL,
        verbose_name=_('執藥方式')
    )
    external_pharmacy = models.ForeignKey(
        'billing.ExternalPharmacy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prescriptions',
        verbose_name=_('外部配藥房')
    )
    
    # 費用
    medicine_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('藥費')
    )
    
    # 狀態
    is_dispensed = models.BooleanField(
        default=False,
        verbose_name=_('是否已配藥')
    )
    dispensed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('配藥時間')
    )
    
    # 稽核日誌
    audit_log = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('修改記錄')
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
    
    class Meta:
        verbose_name = _('處方')
        verbose_name_plural = _('處方')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.prescription_number}"
    
    def save(self, *args, **kwargs):
        if not self.prescription_number:
            # 自動生成處方編號
            from datetime import date
            today = date.today()
            prefix = f"RX{today.strftime('%Y%m%d')}"
            last_rx = Prescription.objects.filter(
                prescription_number__startswith=prefix
            ).order_by('-prescription_number').first()
            
            if last_rx:
                last_num = int(last_rx.prescription_number[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.prescription_number = f"{prefix}{new_num:04d}"
        
        super().save(*args, **kwargs)


class PrescriptionItem(models.Model):
    """
    處方項目（藥品明細）
    """
    
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('處方')
    )
    medicine = models.ForeignKey(
        'inventory.Medicine',
        on_delete=models.PROTECT,
        related_name='prescription_items',
        verbose_name=_('藥品')
    )
    
    # 劑量
    dosage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('劑量')
    )
    unit = models.CharField(
        max_length=20,
        default='克',
        verbose_name=_('單位')
    )
    
    # 煎煮方式（中藥）
    decoction_method = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('煎煮方式')
    )
    
    # 費用
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('單價')
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('小計')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('備註')
    )
    
    class Meta:
        verbose_name = _('處方項目')
        verbose_name_plural = _('處方項目')
        ordering = ['id']
    
    def __str__(self):
        return f"{self.medicine.name} {self.dosage}{self.unit}"
    
    def save(self, *args, **kwargs):
        # 自動計算小計
        self.subtotal = self.dosage * self.unit_price
        super().save(*args, **kwargs)


class ExperienceFormula(models.Model):
    """
    經驗方
    """
    
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'doctor'},
        related_name='experience_formulas',
        verbose_name=_('醫師')
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('方名')
    )
    category = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('分類')
    )
    indication = models.TextField(
        blank=True,
        verbose_name=_('適應症')
    )
    usage_instruction = models.TextField(
        blank=True,
        verbose_name=_('服用方法')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('備註')
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=_('是否公開')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('建立時間')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('更新時間')
    )
    
    class Meta:
        verbose_name = _('經驗方')
        verbose_name_plural = _('經驗方')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ExperienceFormulaItem(models.Model):
    """
    經驗方項目
    """
    
    formula = models.ForeignKey(
        ExperienceFormula,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('經驗方')
    )
    medicine = models.ForeignKey(
        'inventory.Medicine',
        on_delete=models.PROTECT,
        related_name='experience_formula_items',
        verbose_name=_('藥品')
    )
    dosage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('劑量')
    )
    unit = models.CharField(
        max_length=20,
        default='克',
        verbose_name=_('單位')
    )
    decoction_method = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('煎煮方式')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('備註')
    )
    
    class Meta:
        verbose_name = _('經驗方項目')
        verbose_name_plural = _('經驗方項目')
        ordering = ['id']
    
    def __str__(self):
        return f"{self.medicine.name} {self.dosage}{self.unit}"


class Certificate(models.Model):
    """
    證明書
    """
    
    class CertificateType(models.TextChoices):
        MEDICAL = 'medical', _('診斷證明書')
        SICK_LEAVE = 'sick_leave', _('病假證明書')
        REFERRAL = 'referral', _('轉介信')
        OTHER = 'other', _('其他')
    
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name=_('診療記錄')
    )
    certificate_type = models.CharField(
        max_length=20,
        choices=CertificateType.choices,
        verbose_name=_('證明書類型')
    )
    certificate_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('證明書編號')
    )
    content = models.TextField(
        verbose_name=_('內容')
    )
    issue_date = models.DateField(
        verbose_name=_('開立日期')
    )
    
    # 病假相關
    sick_leave_start = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('病假開始日期')
    )
    sick_leave_end = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('病假結束日期')
    )
    
    # 列印記錄
    print_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('列印次數')
    )
    last_printed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('最後列印時間')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('建立時間')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_certificates',
        verbose_name=_('建立者')
    )
    
    class Meta:
        verbose_name = _('證明書')
        verbose_name_plural = _('證明書')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.certificate_number} - {self.get_certificate_type_display()}"

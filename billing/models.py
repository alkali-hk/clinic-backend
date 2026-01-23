"""
Billing models for Clinic Management System.
收款模組 - 收款與派藥訂單管理
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class ChargeItem(models.Model):
    """
    收費項目
    """
    
    class ItemType(models.TextChoices):
        REGISTRATION = 'registration', _('掛號費')
        CONSULTATION = 'consultation', _('診金')
        MEDICINE = 'medicine', _('藥費')
        TREATMENT = 'treatment', _('治療費')
        CERTIFICATE = 'certificate', _('證明書費')
        OTHER = 'other', _('其他')
    
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('項目代碼')
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('項目名稱')
    )
    item_type = models.CharField(
        max_length=20,
        choices=ItemType.choices,
        default=ItemType.OTHER,
        verbose_name=_('項目類型')
    )
    default_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('預設價格')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('是否啟用')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('備註')
    )
    
    class Meta:
        verbose_name = _('收費項目')
        verbose_name_plural = _('收費項目')
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Bill(models.Model):
    """
    帳單
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('待付款')
        PARTIAL = 'partial', _('部分付款')
        PAID = 'paid', _('已付款')
        REFUNDED = 'refunded', _('已退款')
        CANCELLED = 'cancelled', _('已取消')
    
    class PaymentMethod(models.TextChoices):
        CASH = 'cash', _('現金')
        CREDIT_CARD = 'credit_card', _('信用卡')
        DEBIT_CARD = 'debit_card', _('扣帳卡')
        OCTOPUS = 'octopus', _('八達通')
        ALIPAY = 'alipay', _('支付寶')
        WECHAT = 'wechat', _('微信支付')
        BANK_TRANSFER = 'bank_transfer', _('銀行轉帳')
        ACCOUNT_BALANCE = 'account_balance', _('帳戶餘額')
        OTHER = 'other', _('其他')
    
    # 關聯
    registration = models.OneToOneField(
        'registration.Registration',
        on_delete=models.CASCADE,
        related_name='bill',
        verbose_name=_('掛號')
    )
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name='bills',
        verbose_name=_('病患')
    )
    
    # 帳單資訊
    bill_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('帳單編號')
    )
    bill_date = models.DateField(
        verbose_name=_('帳單日期')
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_('狀態')
    )
    
    # 金額
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('小計')
    )
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('折扣')
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('總金額')
    )
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('已付金額')
    )
    balance_due = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('應付餘額')
    )
    
    # 付款資訊
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        blank=True,
        verbose_name=_('付款方式')
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('付款時間')
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
        related_name='created_bills',
        verbose_name=_('建立者')
    )
    
    class Meta:
        verbose_name = _('帳單')
        verbose_name_plural = _('帳單')
        ordering = ['-bill_date', '-created_at']
        indexes = [
            models.Index(fields=['bill_date', 'status']),
            models.Index(fields=['patient', 'bill_date']),
        ]
    
    def __str__(self):
        return f"{self.bill_number}"
    
    def save(self, *args, **kwargs):
        if not self.bill_number:
            # 自動生成帳單編號
            from datetime import date
            today = date.today()
            prefix = f"B{today.strftime('%Y%m%d')}"
            last_bill = Bill.objects.filter(
                bill_number__startswith=prefix
            ).order_by('-bill_number').first()
            
            if last_bill:
                last_num = int(last_bill.bill_number[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.bill_number = f"{prefix}{new_num:04d}"
        
        # 計算餘額
        self.balance_due = self.total_amount - self.paid_amount
        
        super().save(*args, **kwargs)
    
    def calculate_total(self):
        """計算帳單總額"""
        self.subtotal = sum(item.subtotal for item in self.items.all())
        self.total_amount = self.subtotal - self.discount
        self.balance_due = self.total_amount - self.paid_amount
        self.save()


class BillItem(models.Model):
    """
    帳單項目
    """
    
    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('帳單')
    )
    charge_item = models.ForeignKey(
        ChargeItem,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='bill_items',
        verbose_name=_('收費項目')
    )
    prescription = models.ForeignKey(
        'consultation.Prescription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bill_items',
        verbose_name=_('處方')
    )
    
    description = models.CharField(
        max_length=200,
        verbose_name=_('描述')
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        verbose_name=_('數量')
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('單價')
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('小計')
    )
    
    class Meta:
        verbose_name = _('帳單項目')
        verbose_name_plural = _('帳單項目')
    
    def __str__(self):
        return f"{self.description}"
    
    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Payment(models.Model):
    """
    付款記錄
    """
    
    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('帳單')
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('金額')
    )
    payment_method = models.CharField(
        max_length=20,
        choices=Bill.PaymentMethod.choices,
        verbose_name=_('付款方式')
    )
    reference_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('參考編號')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('備註')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('付款時間')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='processed_payments',
        verbose_name=_('收款人員')
    )
    
    class Meta:
        verbose_name = _('付款記錄')
        verbose_name_plural = _('付款記錄')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.bill.bill_number} - {self.amount}"


class Debt(models.Model):
    """
    欠款記錄
    """
    
    class Status(models.TextChoices):
        OUTSTANDING = 'outstanding', _('未清')
        PARTIAL = 'partial', _('部分清償')
        CLEARED = 'cleared', _('已清')
        WRITTEN_OFF = 'written_off', _('已核銷')
    
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name='debts',
        verbose_name=_('病患')
    )
    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name='debts',
        verbose_name=_('帳單')
    )
    original_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('原始欠款金額')
    )
    remaining_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('剩餘欠款金額')
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OUTSTANDING,
        verbose_name=_('狀態')
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('到期日')
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
        verbose_name = _('欠款記錄')
        verbose_name_plural = _('欠款記錄')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient.name} - {self.remaining_amount}"


class ExternalPharmacy(models.Model):
    """
    外部配藥房
    """
    
    class PharmacyType(models.TextChoices):
        DECOCTION = 'decoction', _('煎藥房')
        CONCENTRATE = 'concentrate', _('濃縮配藥房')
    
    name = models.CharField(
        max_length=100,
        verbose_name=_('配藥房名稱')
    )
    pharmacy_type = models.CharField(
        max_length=20,
        choices=PharmacyType.choices,
        verbose_name=_('類型')
    )
    contact_person = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('聯絡人')
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('電話')
    )
    email = models.EmailField(
        blank=True,
        verbose_name=_('電子郵件')
    )
    address = models.TextField(
        blank=True,
        verbose_name=_('地址')
    )
    
    # 費用設定
    processing_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('加工費')
    )
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('運送費')
    )
    
    # API 設定
    api_endpoint = models.URLField(
        blank=True,
        verbose_name=_('API 端點')
    )
    api_key = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('API Key')
    )
    webhook_api_key = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Webhook API Key')
    )
    api_request_format = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('API 請求格式範本')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('是否啟用')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('備註')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('建立時間')
    )
    
    class Meta:
        verbose_name = _('外部配藥房')
        verbose_name_plural = _('外部配藥房')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_pharmacy_type_display()})"


class DispensingOrder(models.Model):
    """
    派藥訂單
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('待發送')
        SENT = 'sent', _('已發送')
        CONFIRMED = 'confirmed', _('對方已確認')
        PROCESSING = 'processing', _('配藥中')
        SHIPPED = 'shipped', _('已發貨')
        COMPLETED = 'completed', _('已完成')
        FAILED = 'failed', _('失敗')
        CANCELLED = 'cancelled', _('已取消')
    
    # 關聯
    prescription = models.ForeignKey(
        'consultation.Prescription',
        on_delete=models.CASCADE,
        related_name='dispensing_orders',
        verbose_name=_('處方')
    )
    external_pharmacy = models.ForeignKey(
        ExternalPharmacy,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name=_('外部配藥房')
    )
    
    # 訂單資訊
    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('訂單編號')
    )
    client_order_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('客戶訂單 ID')
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_('狀態')
    )
    
    # 費用
    medicine_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('藥費')
    )
    processing_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('加工費')
    )
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('運送費')
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('總金額')
    )
    
    # 配送資訊
    recipient_name = models.CharField(
        max_length=100,
        verbose_name=_('收件人姓名')
    )
    recipient_phone = models.CharField(
        max_length=20,
        verbose_name=_('收件人電話')
    )
    recipient_address = models.TextField(
        verbose_name=_('收件地址')
    )
    
    # 物流資訊
    tracking_company = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('物流公司')
    )
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('運單號碼')
    )
    
    # API 回應
    api_response = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('API 回應')
    )
    error_message = models.TextField(
        blank=True,
        verbose_name=_('錯誤訊息')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('備註')
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('發送時間')
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('完成時間')
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
        related_name='created_dispensing_orders',
        verbose_name=_('建立者')
    )
    
    class Meta:
        verbose_name = _('派藥訂單')
        verbose_name_plural = _('派藥訂單')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['external_pharmacy', 'status']),
        ]
    
    def __str__(self):
        return f"{self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # 自動生成訂單編號
            import uuid
            from datetime import date
            today = date.today()
            prefix = f"DO{today.strftime('%Y%m%d')}"
            last_order = DispensingOrder.objects.filter(
                order_number__startswith=prefix
            ).order_by('-order_number').first()
            
            if last_order:
                last_num = int(last_order.order_number[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.order_number = f"{prefix}{new_num:04d}"
        
        if not self.client_order_id:
            import uuid
            self.client_order_id = str(uuid.uuid4()).upper()
        
        # 計算總金額
        self.total_amount = self.medicine_fee + self.processing_fee + self.delivery_fee
        
        super().save(*args, **kwargs)

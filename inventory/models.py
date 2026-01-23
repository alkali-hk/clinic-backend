"""
Inventory models for Clinic Management System.
庫存模組 - 藥品與庫存管理
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class MedicineCategory(models.Model):
    """
    藥品分類
    """
    
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('分類名稱')
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_('分類代碼')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('描述')
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('上層分類')
    )
    
    class Meta:
        verbose_name = _('藥品分類')
        verbose_name_plural = _('藥品分類')
        ordering = ['code']
    
    def __str__(self):
        return self.name


class Supplier(models.Model):
    """
    供應商
    """
    
    name = models.CharField(
        max_length=100,
        verbose_name=_('供應商名稱')
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('供應商代碼')
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
    fax = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('傳真')
    )
    email = models.EmailField(
        blank=True,
        verbose_name=_('電子郵件')
    )
    address = models.TextField(
        blank=True,
        verbose_name=_('地址')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('備註')
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
        verbose_name = _('供應商')
        verbose_name_plural = _('供應商')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Medicine(models.Model):
    """
    藥品
    """
    
    class MedicineType(models.TextChoices):
        HERB = 'herb', _('中藥飲片')
        CONCENTRATE = 'concentrate', _('濃縮中藥')
        WESTERN = 'western', _('西藥')
        SUPPLEMENT = 'supplement', _('保健品')
        OTHER = 'other', _('其他')
    
    # 基本資料
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('藥品代碼')
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('藥品名稱')
    )
    english_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('英文名稱')
    )
    pinyin = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('拼音')
    )
    
    # 分類
    medicine_type = models.CharField(
        max_length=20,
        choices=MedicineType.choices,
        default=MedicineType.CONCENTRATE,
        verbose_name=_('藥品類型')
    )
    category = models.ForeignKey(
        MedicineCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medicines',
        verbose_name=_('分類')
    )
    
    # 規格
    specification = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('規格')
    )
    unit = models.CharField(
        max_length=20,
        default='克',
        verbose_name=_('單位')
    )
    package_unit = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('包裝單位')
    )
    package_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        verbose_name=_('包裝數量')
    )
    
    # 品牌與供應商
    brand = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('品牌')
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medicines',
        verbose_name=_('供應商')
    )
    
    # 價格
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('成本價')
    )
    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('售價')
    )
    
    # 庫存設定
    safety_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('安全庫存量')
    )
    
    # 藥理資訊
    properties = models.TextField(
        blank=True,
        verbose_name=_('性味')
    )
    meridians = models.TextField(
        blank=True,
        verbose_name=_('歸經')
    )
    functions = models.TextField(
        blank=True,
        verbose_name=_('功效')
    )
    indications = models.TextField(
        blank=True,
        verbose_name=_('主治')
    )
    contraindications = models.TextField(
        blank=True,
        verbose_name=_('禁忌')
    )
    dosage_guide = models.TextField(
        blank=True,
        verbose_name=_('用量指引')
    )
    
    # 外部 SKU（用於對接外部系統）
    external_sku = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('外部 SKU')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('備註')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('是否啟用')
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
        verbose_name = _('藥品')
        verbose_name_plural = _('藥品')
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
            models.Index(fields=['pinyin']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Inventory(models.Model):
    """
    庫存
    """
    
    medicine = models.OneToOneField(
        Medicine,
        on_delete=models.CASCADE,
        related_name='inventory',
        verbose_name=_('藥品')
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('庫存數量')
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_('最後更新時間')
    )
    
    class Meta:
        verbose_name = _('庫存')
        verbose_name_plural = _('庫存')
    
    def __str__(self):
        return f"{self.medicine.name}: {self.quantity}{self.medicine.unit}"
    
    @property
    def is_low_stock(self):
        """檢查是否低於安全庫存"""
        return self.quantity < self.medicine.safety_stock


class InventoryTransaction(models.Model):
    """
    庫存異動記錄
    """
    
    class TransactionType(models.TextChoices):
        PURCHASE = 'purchase', _('進貨')
        DISPENSE = 'dispense', _('配藥扣減')
        ADJUSTMENT = 'adjustment', _('盤點調整')
        RETURN = 'return', _('退貨')
        DAMAGE = 'damage', _('損耗')
        TRANSFER = 'transfer', _('調撥')
    
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name=_('藥品')
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        verbose_name=_('異動類型')
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('數量')
    )
    before_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('異動前數量')
    )
    after_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('異動後數量')
    )
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('單位成本')
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
        verbose_name=_('建立時間')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='inventory_transactions',
        verbose_name=_('操作人員')
    )
    
    class Meta:
        verbose_name = _('庫存異動')
        verbose_name_plural = _('庫存異動')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['medicine', 'created_at']),
            models.Index(fields=['transaction_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.medicine.name} {self.get_transaction_type_display()} {self.quantity}"


class PurchaseOrder(models.Model):
    """
    進貨單
    """
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('草稿')
        SUBMITTED = 'submitted', _('已提交')
        RECEIVED = 'received', _('已收貨')
        CANCELLED = 'cancelled', _('已取消')
    
    order_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('進貨單號')
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        verbose_name=_('供應商')
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_('狀態')
    )
    order_date = models.DateField(
        verbose_name=_('訂購日期')
    )
    expected_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('預計到貨日期')
    )
    received_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('實際到貨日期')
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('總金額')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('備註')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('建立時間')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_purchase_orders',
        verbose_name=_('建立者')
    )
    
    class Meta:
        verbose_name = _('進貨單')
        verbose_name_plural = _('進貨單')
        ordering = ['-order_date']
    
    def __str__(self):
        return self.order_number


class PurchaseOrderItem(models.Model):
    """
    進貨單項目
    """
    
    order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('進貨單')
    )
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.PROTECT,
        related_name='purchase_items',
        verbose_name=_('藥品')
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
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
    received_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('已收數量')
    )
    
    class Meta:
        verbose_name = _('進貨單項目')
        verbose_name_plural = _('進貨單項目')
    
    def __str__(self):
        return f"{self.medicine.name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class CompoundFormula(models.Model):
    """
    複方成份設定
    用於定義複方藥品的成份組成
    """
    
    compound_medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name='compound_formulas',
        verbose_name=_('複方藥品')
    )
    ingredient_medicine = models.ForeignKey(
        Medicine,
        on_delete=models.PROTECT,
        related_name='as_ingredient_in',
        verbose_name=_('成份藥品')
    )
    ratio = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        verbose_name=_('比例')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('備註')
    )
    
    class Meta:
        verbose_name = _('複方成份')
        verbose_name_plural = _('複方成份')
        unique_together = ['compound_medicine', 'ingredient_medicine']
    
    def __str__(self):
        return f"{self.compound_medicine.name} - {self.ingredient_medicine.name}"

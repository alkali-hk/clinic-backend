#!/usr/bin/env python
"""
Initialize production data for Clinic Management System
診所管理系統 - 生產環境初始化資料腳本
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import SystemSetting, DiagnosisCode
from inventory.models import Medicine, Supplier
from consultation.models import ExperienceFormula
from decimal import Decimal

User = get_user_model()

def create_superuser():
    """Create admin superuser if not exists"""
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@clinic.com',
            password='admin123',
            full_name='系統管理員',
            role='admin'
        )
        print('✓ Created superuser: admin / admin123')
    else:
        print('✓ Superuser already exists')

def create_system_settings():
    """Create default system settings"""
    settings = [
        ('clinic_name', '診所管理系統', '診所名稱'),
        ('clinic_address', '香港九龍區', '診所地址'),
        ('clinic_phone', '12345678', '診所電話'),
        ('consultation_fee', '300', '診金'),
        ('medicine_markup', '1.5', '藥品加成比例'),
    ]
    
    for key, value, description in settings:
        obj, created = SystemSetting.objects.get_or_create(
            key=key,
            defaults={'value': value, 'description': description}
        )
        if created:
            print(f'✓ Created setting: {key}')

def create_diagnosis_codes():
    """Create sample diagnosis codes"""
    codes = [
        ('A01', '感冒', '普通感冒'),
        ('A02', '咳嗽', '咳嗽症狀'),
        ('A03', '頭痛', '頭痛症狀'),
        ('A04', '胃痛', '胃部不適'),
        ('A05', '失眠', '睡眠障礙'),
        ('B01', '高血壓', '血壓偏高'),
        ('B02', '糖尿病', '血糖異常'),
        ('C01', '腰痛', '腰部疼痛'),
        ('C02', '關節炎', '關節發炎'),
    ]
    
    for code, name, description in codes:
        obj, created = DiagnosisCode.objects.get_or_create(
            code=code,
            defaults={'name': name, 'description': description}
        )
        if created:
            print(f'✓ Created diagnosis code: {code} - {name}')

def create_suppliers():
    """Create sample suppliers"""
    suppliers = [
        ('SUP001', '大藥行', '香港九龍區藥材街1號', '12345678', 'supplier1@example.com'),
        ('SUP002', '中藥批發商', '香港新界區中藥城2號', '87654321', 'supplier2@example.com'),
    ]
    
    for code, name, address, phone, email in suppliers:
        obj, created = Supplier.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'address': address,
                'phone': phone,
                'email': email
            }
        )
        if created:
            print(f'✓ Created supplier: {name}')

def create_medicines():
    """Create sample medicines"""
    medicines = [
        ('MED001', '感冒靈', '顆粒', '盒', Decimal('50.00'), Decimal('35.00'), 100, 20),
        ('MED002', '止咳糖漿', '液體', '瓶', Decimal('80.00'), Decimal('55.00'), 50, 10),
        ('MED003', '頭痛片', '片劑', '盒', Decimal('45.00'), Decimal('30.00'), 200, 30),
        ('MED004', '胃藥', '片劑', '盒', Decimal('60.00'), Decimal('40.00'), 150, 25),
        ('MED005', '安神丸', '丸劑', '瓶', Decimal('120.00'), Decimal('85.00'), 80, 15),
        ('MED006', '黃芪', '中藥材', '克', Decimal('0.50'), Decimal('0.30'), 5000, 500),
        ('MED007', '當歸', '中藥材', '克', Decimal('0.80'), Decimal('0.50'), 3000, 300),
        ('MED008', '枸杞', '中藥材', '克', Decimal('0.60'), Decimal('0.40'), 4000, 400),
    ]
    
    for code, name, form, unit, price, cost, stock, safety in medicines:
        obj, created = Medicine.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'form': form,
                'unit': unit,
                'unit_price': price,
                'cost_price': cost,
                'stock_quantity': stock,
                'safety_stock': safety,
                'is_active': True
            }
        )
        if created:
            print(f'✓ Created medicine: {name}')

def create_experience_formulas():
    """Create sample experience formulas"""
    formulas = [
        ('EXP001', '感冒方', '感冒初期', '黃芪10g, 當歸5g, 枸杞8g'),
        ('EXP002', '止咳方', '咳嗽痰多', '止咳糖漿 3次/日'),
        ('EXP003', '安神方', '失眠多夢', '安神丸 2次/日'),
    ]
    
    for code, name, indication, content in formulas:
        obj, created = ExperienceFormula.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'indication': indication,
                'content': content,
                'is_active': True
            }
        )
        if created:
            print(f'✓ Created experience formula: {name}')

def main():
    print('='*50)
    print('Initializing Production Data')
    print('='*50)
    
    create_superuser()
    create_system_settings()
    create_diagnosis_codes()
    create_suppliers()
    create_medicines()
    create_experience_formulas()
    
    print('='*50)
    print('Production data initialization complete!')
    print('='*50)

if __name__ == '__main__':
    main()

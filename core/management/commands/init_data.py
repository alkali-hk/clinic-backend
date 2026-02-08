"""
Django management command to initialize production data.
Usage: python manage.py init_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import SystemSetting, DiagnosisCode
from inventory.models import Medicine, Supplier
from consultation.models import ExperienceFormula
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Initialize production data for Clinic Management System'

    def handle(self, *args, **options):
        self.stdout.write('=' * 50)
        self.stdout.write('Initializing Production Data')
        self.stdout.write('=' * 50)

        self.create_superuser()
        self.create_system_settings()
        self.create_diagnosis_codes()
        self.create_suppliers()
        self.create_medicines()
        self.create_experience_formulas()

        self.stdout.write('=' * 50)
        self.stdout.write(self.style.SUCCESS('Production data initialization complete!'))
        self.stdout.write('=' * 50)

    def create_superuser(self):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@clinic.com',
                password='admin123',
                first_name='系統',
                last_name='管理員',
                role='admin'
            )
            self.stdout.write(self.style.SUCCESS('Created superuser: admin / admin123'))
        else:
            self.stdout.write('Superuser already exists')

    def create_system_settings(self):
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
                self.stdout.write(self.style.SUCCESS(f'Created setting: {key}'))

    def create_diagnosis_codes(self):
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
                self.stdout.write(self.style.SUCCESS(f'Created diagnosis code: {code} - {name}'))

    def create_suppliers(self):
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
                self.stdout.write(self.style.SUCCESS(f'Created supplier: {name}'))

    def create_medicines(self):
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
                self.stdout.write(self.style.SUCCESS(f'Created medicine: {name}'))

    def create_experience_formulas(self):
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
                self.stdout.write(self.style.SUCCESS(f'Created experience formula: {name}'))

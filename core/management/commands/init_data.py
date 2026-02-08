"""
Django management command to initialize production data.
Usage: python manage.py init_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Initialize production data for Clinic Management System'

    def handle(self, *args, **options):
        self.stdout.write('=' * 50)
        self.stdout.write('Initializing Production Data')
        self.stdout.write('=' * 50)

        self.create_superuser()
        self.create_clinic_settings()
        self.create_diagnostic_terms()
        self.create_suppliers()
        self.create_medicines()

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

    def create_clinic_settings(self):
        try:
            from core.models import ClinicSettings
            if not ClinicSettings.objects.exists():
                ClinicSettings.objects.create(
                    clinic_name='診所管理系統',
                    address='香港九龍區',
                    phone='12345678',
                )
                self.stdout.write(self.style.SUCCESS('Created clinic settings'))
            else:
                self.stdout.write('Clinic settings already exist')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Skipped clinic settings: {e}'))

    def create_diagnostic_terms(self):
        try:
            from consultation.models import DiagnosticTerm
            terms = [
                ('感冒', '普通感冒'),
                ('咳嗽', '咳嗽症狀'),
                ('頭痛', '頭痛症狀'),
                ('胃痛', '胃部不適'),
                ('失眠', '睡眠障礙'),
                ('高血壓', '血壓偏高'),
                ('糖尿病', '血糖異常'),
                ('腰痛', '腰部疼痛'),
                ('關節炎', '關節發炎'),
            ]
            for name, description in terms:
                obj, created = DiagnosticTerm.objects.get_or_create(
                    name=name,
                    defaults={'description': description}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created diagnostic term: {name}'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Skipped diagnostic terms: {e}'))

    def create_suppliers(self):
        try:
            from inventory.models import Supplier
            suppliers = [
                ('大藥行', '香港九龍區藥材街1號', '12345678', 'supplier1@example.com'),
                ('中藥批發商', '香港新界區中藥城2號', '87654321', 'supplier2@example.com'),
            ]
            for name, address, phone, email in suppliers:
                obj, created = Supplier.objects.get_or_create(
                    name=name,
                    defaults={
                        'address': address,
                        'phone': phone,
                        'email': email
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created supplier: {name}'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Skipped suppliers: {e}'))

    def create_medicines(self):
        try:
            from inventory.models import Medicine
            from decimal import Decimal
            medicines = [
                ('感冒靈', '顆粒', '盒', Decimal('50.00'), Decimal('35.00'), 100),
                ('止咳糖漿', '液體', '瓶', Decimal('80.00'), Decimal('55.00'), 50),
                ('頭痛片', '片劑', '盒', Decimal('45.00'), Decimal('30.00'), 200),
                ('胃藥', '片劑', '盒', Decimal('60.00'), Decimal('40.00'), 150),
                ('安神丸', '丸劑', '瓶', Decimal('120.00'), Decimal('85.00'), 80),
                ('黃芪', '中藥材', '克', Decimal('0.50'), Decimal('0.30'), 5000),
                ('當歸', '中藥材', '克', Decimal('0.80'), Decimal('0.50'), 3000),
                ('枸杞', '中藥材', '克', Decimal('0.60'), Decimal('0.40'), 4000),
            ]
            for name, form, unit, price, cost, stock in medicines:
                obj, created = Medicine.objects.get_or_create(
                    name=name,
                    defaults={
                        'unit': unit,
                        'unit_price': price,
                        'stock_quantity': stock,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created medicine: {name}'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Skipped medicines: {e}'))

"""
Create test data for the clinic system
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from patients.models import Patient
from inventory.models import Medicine, Inventory, Supplier, MedicineCategory
from registration.models import Registration, Appointment
from consultation.models import DiagnosticTerm
from core.models import ClinicRoom, Schedule
from datetime import date, time, timedelta
from decimal import Decimal

User = get_user_model()

# Create doctor user
doctor, created = User.objects.get_or_create(
    username='doctor1',
    defaults={
        'email': 'doctor1@clinic.com',
        'first_name': '張',
        'last_name': '醫師',
        'role': 'doctor',
        'is_staff': True,
    }
)
if created:
    doctor.set_password('doctor123')
    doctor.save()
    print("Created doctor: doctor1 / doctor123")

# Create receptionist user
receptionist, created = User.objects.get_or_create(
    username='reception1',
    defaults={
        'email': 'reception1@clinic.com',
        'first_name': '李',
        'last_name': '小姐',
        'role': 'assistant',
    }
)
if created:
    receptionist.set_password('reception123')
    receptionist.save()
    print("Created receptionist: reception1 / reception123")

# Create clinic rooms
room1, _ = ClinicRoom.objects.get_or_create(
    code='R101',
    defaults={'name': '診間一', 'is_active': True}
)
room2, _ = ClinicRoom.objects.get_or_create(
    code='R102',
    defaults={'name': '診間二', 'is_active': True}
)
print("Created clinic rooms")

# Create categories
cat_herb, _ = MedicineCategory.objects.get_or_create(name='中藥材', defaults={'code': 'HERB'})
cat_conc, _ = MedicineCategory.objects.get_or_create(name='濃縮中藥', defaults={'code': 'CONC'})
print("Created categories")

# Create supplier
supplier, _ = Supplier.objects.get_or_create(
    name='順天堂',
    defaults={
        'code': 'STT',
        'contact_person': '王經理',
        'phone': '02-12345678',
        'email': 'order@stt.com.tw',
        'address': '台北市中正區',
        'is_active': True
    }
)
print("Created supplier")

# Create medicines
medicines_data = [
    {'code': 'HB001', 'name': '黃耆', 'pinyin': 'huangqi', 'category': cat_herb, 'unit': 'g', 'cost': 0.5, 'price': 1.0},
    {'code': 'HB002', 'name': '當歸', 'pinyin': 'danggui', 'category': cat_herb, 'unit': 'g', 'cost': 0.8, 'price': 1.5},
    {'code': 'HB003', 'name': '川芎', 'pinyin': 'chuanxiong', 'category': cat_herb, 'unit': 'g', 'cost': 0.6, 'price': 1.2},
    {'code': 'HB004', 'name': '白芍', 'pinyin': 'baishao', 'category': cat_herb, 'unit': 'g', 'cost': 0.4, 'price': 0.8},
    {'code': 'HB005', 'name': '熟地黃', 'pinyin': 'shudihuang', 'category': cat_herb, 'unit': 'g', 'cost': 0.7, 'price': 1.3},
    {'code': 'HB006', 'name': '人參', 'pinyin': 'renshen', 'category': cat_herb, 'unit': 'g', 'cost': 5.0, 'price': 10.0},
    {'code': 'HB007', 'name': '甘草', 'pinyin': 'gancao', 'category': cat_herb, 'unit': 'g', 'cost': 0.2, 'price': 0.5},
    {'code': 'HB008', 'name': '茯苓', 'pinyin': 'fuling', 'category': cat_herb, 'unit': 'g', 'cost': 0.3, 'price': 0.6},
    {'code': 'HB009', 'name': '白朮', 'pinyin': 'baizhu', 'category': cat_herb, 'unit': 'g', 'cost': 0.4, 'price': 0.8},
    {'code': 'HB010', 'name': '桂枝', 'pinyin': 'guizhi', 'category': cat_herb, 'unit': 'g', 'cost': 0.3, 'price': 0.6},
    {'code': 'CF001', 'name': '四物湯', 'pinyin': 'siwutang', 'category': cat_conc, 'unit': 'g', 'cost': 1.0, 'price': 2.0},
    {'code': 'CF002', 'name': '補中益氣湯', 'pinyin': 'buzhongyiqitang', 'category': cat_conc, 'unit': 'g', 'cost': 1.2, 'price': 2.5},
    {'code': 'CF003', 'name': '六君子湯', 'pinyin': 'liujunzitang', 'category': cat_conc, 'unit': 'g', 'cost': 1.0, 'price': 2.0},
    {'code': 'CF004', 'name': '桂枝湯', 'pinyin': 'guizhitang', 'category': cat_conc, 'unit': 'g', 'cost': 0.8, 'price': 1.5},
    {'code': 'CF005', 'name': '小柴胡湯', 'pinyin': 'xiaochaihutang', 'category': cat_conc, 'unit': 'g', 'cost': 1.0, 'price': 2.0},
]

for med_data in medicines_data:
    med, created = Medicine.objects.get_or_create(
        code=med_data['code'],
        defaults={
            'name': med_data['name'],
            'pinyin': med_data['pinyin'],
            'category': med_data['category'],
            'unit': med_data['unit'],
            'cost_price': Decimal(str(med_data['cost'])),
            'selling_price': Decimal(str(med_data['price'])),
            'safety_stock': Decimal('100'),
            'is_active': True
        }
    )
    if created:
        # Create inventory
        Inventory.objects.create(
            medicine=med,
            quantity=Decimal('1000'),
            
            
        )
print(f"Created {len(medicines_data)} medicines with inventory")

# Create diagnostic terms
terms_data = [
    {'category': 'symptom', 'code': 'SY001', 'name': '頭痛'},
    {'category': 'symptom', 'code': 'SY002', 'name': '發熱'},
    {'category': 'symptom', 'code': 'SY003', 'name': '咳嗽'},
    {'category': 'symptom', 'code': 'SY004', 'name': '失眠'},
    {'category': 'symptom', 'code': 'SY005', 'name': '疲勞'},
    {'category': 'tongue', 'code': 'TG001', 'name': '舌紅'},
    {'category': 'tongue', 'code': 'TG002', 'name': '舌淡'},
    {'category': 'tongue', 'code': 'TG003', 'name': '苔白'},
    {'category': 'tongue', 'code': 'TG004', 'name': '苔黃'},
    {'category': 'pulse', 'code': 'PL001', 'name': '脈浮'},
    {'category': 'pulse', 'code': 'PL002', 'name': '脈沉'},
    {'category': 'pulse', 'code': 'PL003', 'name': '脈數'},
    {'category': 'pulse', 'code': 'PL004', 'name': '脈細'},
    {'category': 'syndrome', 'code': 'SD001', 'name': '氣虛'},
    {'category': 'syndrome', 'code': 'SD002', 'name': '血虛'},
    {'category': 'syndrome', 'code': 'SD003', 'name': '陰虛'},
    {'category': 'syndrome', 'code': 'SD004', 'name': '陽虛'},
    {'category': 'syndrome', 'code': 'SD005', 'name': '濕熱'},
]

for term_data in terms_data:
    DiagnosticTerm.objects.get_or_create(
        code=term_data['code'],
        defaults={
            'category': term_data['category'],
            'name': term_data['name'],
            'is_active': True
        }
    )
print(f"Created {len(terms_data)} diagnostic terms")

# Create patients
patients_data = [
    {'chart_number': 'P20260001', 'name': '王小明', 'gender': 'male', 'birth_date': date(1985, 5, 15), 'phone': '0912345678', 'id_card_number': 'A123456789'},
    {'chart_number': 'P20260002', 'name': '李美玲', 'gender': 'female', 'birth_date': date(1990, 8, 20), 'phone': '0923456789', 'id_card_number': 'B234567890'},
    {'chart_number': 'P20260003', 'name': '張大偉', 'gender': 'male', 'birth_date': date(1978, 3, 10), 'phone': '0934567890', 'id_card_number': 'C345678901'},
    {'chart_number': 'P20260004', 'name': '陳淑芬', 'gender': 'female', 'birth_date': date(1995, 12, 5), 'phone': '0945678901', 'id_card_number': 'D456789012'},
    {'chart_number': 'P20260005', 'name': '林志豪', 'gender': 'male', 'birth_date': date(1982, 7, 25), 'phone': '0956789012', 'id_card_number': 'E567890123'},
]

for p_data in patients_data:
    Patient.objects.get_or_create(
        chart_number=p_data['chart_number'],
        defaults=p_data
    )
print(f"Created {len(patients_data)} patients")

# Create today's registrations
today = date.today()
patients = Patient.objects.all()[:3]
for i, patient in enumerate(patients):
    reg, created = Registration.objects.get_or_create(
        patient=patient,
        registration_date=today,
        defaults={
            'doctor': doctor,
            'room': room1,
            'visit_type': 'follow_up' if i > 0 else 'first_visit',
            'queue_number': i + 1,
            'status': 'waiting',
            'created_by': receptionist
        }
    )
    if created:
        print(f"Created registration for {patient.name}")

print("\n=== Test data creation completed ===")
print("Doctor login: doctor1 / doctor123")
print("Receptionist login: reception1 / reception123")

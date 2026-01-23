#!/usr/bin/env python3
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/home/ubuntu/clinic-system/backend')
django.setup()

from datetime import date
from registration.models import Registration
from billing.models import Bill, BillItem
from consultation.models import Consultation, Prescription
from core.models import User

# 獲取一個掛號記錄
registration = Registration.objects.first()
if registration:
    print(f"Registration: {registration.id}, Patient: {registration.patient.name}, Status: {registration.status}")
    
    # 檢查是否已有帳單
    existing_bill = Bill.objects.filter(registration=registration).first()
    if existing_bill:
        print(f"Existing Bill: {existing_bill.bill_number}, Total: {existing_bill.total_amount}")
    else:
        print("No existing bill, creating one...")
        
        # 計算費用
        consultation_fee = 300
        medicine_fee = 0
        
        # 取得診療記錄和處方
        consultation = Consultation.objects.filter(registration=registration).first()
        if consultation:
            print(f"Consultation found: {consultation.id}")
            prescriptions = Prescription.objects.filter(consultation=consultation)
            for prescription in prescriptions:
                medicine_fee += float(prescription.medicine_fee or 0)
                print(f"Prescription: {prescription.id}, Medicine Fee: {prescription.medicine_fee}")
        
        total_amount = consultation_fee + medicine_fee
        
        # 建立帳單
        admin_user = User.objects.filter(is_superuser=True).first()
        bill = Bill.objects.create(
            registration=registration,
            patient=registration.patient,
            bill_date=date.today(),
            subtotal=total_amount,
            total_amount=total_amount,
            paid_amount=0,
            balance_due=total_amount,
            status=Bill.Status.PENDING,
            created_by=admin_user
        )
        print(f"Created Bill: {bill.bill_number}, Total: {bill.total_amount}")
        
        # 建立帳單項目
        BillItem.objects.create(
            bill=bill,
            description='診金',
            quantity=1,
            unit_price=consultation_fee,
            subtotal=consultation_fee
        )
        
        if medicine_fee > 0:
            BillItem.objects.create(
                bill=bill,
                description='藥費',
                quantity=1,
                unit_price=medicine_fee,
                subtotal=medicine_fee
            )
else:
    print("No registration found")

# 列出所有帳單
print("\nAll Bills:")
for bill in Bill.objects.all():
    print(f"  {bill.bill_number}: {bill.patient.name}, Total: {bill.total_amount}, Status: {bill.status}")

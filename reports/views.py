"""
Reports module views.
"""

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDate
from datetime import date, timedelta
from .models import ReportTemplate, GeneratedReport
from .serializers import ReportTemplateSerializer, GeneratedReportSerializer


class ReportTemplateViewSet(viewsets.ModelViewSet):
    """報表範本管理"""
    queryset = ReportTemplate.objects.all()
    serializer_class = ReportTemplateSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['report_type', 'is_active']
    search_fields = ['name']


class GeneratedReportViewSet(viewsets.ReadOnlyModelViewSet):
    """已生成報表（只讀）"""
    queryset = GeneratedReport.objects.select_related('template', 'generated_by')
    serializer_class = GeneratedReportSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['template']
    ordering_fields = ['generated_at']
    ordering = ['-generated_at']


class DailySummaryReportView(APIView):
    """每日結算報表"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from datetime import datetime
        
        date_str = request.query_params.get('date')
        if date_str:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            target_date = date.today()
        
        from registration.models import Registration
        from billing.models import Bill, Payment
        from consultation.models import Prescription
        
        # 掛號統計
        registrations = Registration.objects.filter(registration_date=target_date)
        reg_stats = {
            'total': registrations.count(),
            'first_visit': registrations.filter(visit_type='first_visit').count(),
            'follow_up': registrations.filter(visit_type='follow_up').count(),
            'completed': registrations.filter(status='completed').count(),
            'cancelled': registrations.filter(status='cancelled').count(),
        }
        
        # 收款統計
        bills = Bill.objects.filter(bill_date=target_date)
        payments = Payment.objects.filter(created_at__date=target_date, amount__gt=0)
        
        revenue_stats = {
            'total_billed': float(bills.aggregate(total=Sum('total_amount'))['total'] or 0),
            'total_collected': float(payments.aggregate(total=Sum('amount'))['total'] or 0),
            'outstanding': float(bills.filter(status='pending').aggregate(total=Sum('balance_due'))['total'] or 0),
        }
        
        # 付款方式分佈
        payment_methods = {}
        for payment in payments:
            method = payment.get_payment_method_display()
            if method not in payment_methods:
                payment_methods[method] = 0
            payment_methods[method] += float(payment.amount)
        
        # 處方統計
        prescriptions = Prescription.objects.filter(created_at__date=target_date)
        rx_stats = {
            'total': prescriptions.count(),
            'internal': prescriptions.filter(dispensing_method='internal').count(),
            'external_decoction': prescriptions.filter(dispensing_method='external_decoction').count(),
            'external_concentrate': prescriptions.filter(dispensing_method='external_concentrate').count(),
        }
        
        return Response({
            'date': target_date,
            'registrations': reg_stats,
            'revenue': revenue_stats,
            'payment_methods': payment_methods,
            'prescriptions': rx_stats,
        })


class MonthlySummaryReportView(APIView):
    """月結報表"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        year = int(request.query_params.get('year', date.today().year))
        month = int(request.query_params.get('month', date.today().month))
        
        from registration.models import Registration
        from billing.models import Bill, Payment
        
        # 計算月份的開始和結束日期
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # 每日統計
        daily_stats = []
        current_date = start_date
        while current_date <= end_date:
            registrations = Registration.objects.filter(registration_date=current_date)
            payments = Payment.objects.filter(created_at__date=current_date, amount__gt=0)
            
            daily_stats.append({
                'date': current_date,
                'registrations': registrations.count(),
                'revenue': float(payments.aggregate(total=Sum('amount'))['total'] or 0),
            })
            current_date += timedelta(days=1)
        
        # 月度總計
        registrations = Registration.objects.filter(
            registration_date__gte=start_date,
            registration_date__lte=end_date
        )
        payments = Payment.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            amount__gt=0
        )
        
        summary = {
            'year': year,
            'month': month,
            'total_registrations': registrations.count(),
            'total_revenue': float(payments.aggregate(total=Sum('amount'))['total'] or 0),
            'average_daily_registrations': round(registrations.count() / len(daily_stats), 1),
            'average_daily_revenue': round(float(payments.aggregate(total=Sum('amount'))['total'] or 0) / len(daily_stats), 2),
        }
        
        return Response({
            'summary': summary,
            'daily_stats': daily_stats,
        })


class DoctorWorkloadReportView(APIView):
    """醫師工作量報表"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from datetime import datetime
        
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = date.today() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            end_date = date.today()
        
        from registration.models import Registration
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        doctors = User.objects.filter(role='doctor', is_active=True)
        
        doctor_stats = []
        for doctor in doctors:
            registrations = Registration.objects.filter(
                doctor=doctor,
                registration_date__gte=start_date,
                registration_date__lte=end_date
            )
            
            completed = registrations.filter(status='completed')
            
            # 計算平均看診時間
            avg_time = None
            times = []
            for reg in completed:
                if reg.consultation_start_time and reg.consultation_end_time:
                    duration = (reg.consultation_end_time - reg.consultation_start_time).total_seconds() / 60
                    times.append(duration)
            if times:
                avg_time = round(sum(times) / len(times), 1)
            
            doctor_stats.append({
                'doctor_id': doctor.id,
                'doctor_name': doctor.get_full_name(),
                'total_registrations': registrations.count(),
                'completed': completed.count(),
                'first_visit': registrations.filter(visit_type='first_visit').count(),
                'follow_up': registrations.filter(visit_type='follow_up').count(),
                'average_consultation_time_minutes': avg_time,
            })
        
        return Response({
            'period': {
                'start_date': start_date,
                'end_date': end_date,
            },
            'doctors': doctor_stats,
        })


class MedicineUsageReportView(APIView):
    """藥品使用統計報表"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from datetime import datetime
        
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = date.today() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            end_date = date.today()
        
        from consultation.models import PrescriptionItem
        from inventory.models import Medicine
        
        # 藥品使用量統計
        usage_stats = PrescriptionItem.objects.filter(
            prescription__created_at__date__gte=start_date,
            prescription__created_at__date__lte=end_date,
            prescription__is_dispensed=True
        ).values(
            'medicine__id', 'medicine__code', 'medicine__name', 'unit'
        ).annotate(
            total_quantity=Sum('dosage'),
            prescription_count=Count('prescription', distinct=True)
        ).order_by('-total_quantity')[:50]
        
        return Response({
            'period': {
                'start_date': start_date,
                'end_date': end_date,
            },
            'usage_stats': list(usage_stats),
        })


class ExternalPharmacyReconciliationView(APIView):
    """外部配藥房對帳報表"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from datetime import datetime
        
        pharmacy_id = request.query_params.get('pharmacy_id')
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = date.today() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            end_date = date.today()
        
        from billing.models import DispensingOrder, ExternalPharmacy
        
        queryset = DispensingOrder.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            status__in=['completed', 'shipped']
        )
        
        if pharmacy_id:
            queryset = queryset.filter(external_pharmacy_id=pharmacy_id)
        
        # 按配藥房分組統計
        pharmacy_stats = queryset.values(
            'external_pharmacy__id', 'external_pharmacy__name'
        ).annotate(
            order_count=Count('id'),
            total_medicine_fee=Sum('medicine_fee'),
            total_processing_fee=Sum('processing_fee'),
            total_delivery_fee=Sum('delivery_fee'),
            total_amount=Sum('total_amount')
        )
        
        # 訂單明細
        orders = queryset.select_related('prescription', 'external_pharmacy').order_by('-created_at')
        order_details = []
        for order in orders:
            order_details.append({
                'order_number': order.order_number,
                'prescription_number': order.prescription.prescription_number,
                'pharmacy_name': order.external_pharmacy.name,
                'status': order.get_status_display(),
                'medicine_fee': float(order.medicine_fee),
                'processing_fee': float(order.processing_fee),
                'delivery_fee': float(order.delivery_fee),
                'total_amount': float(order.total_amount),
                'created_at': order.created_at,
                'completed_at': order.completed_at,
            })
        
        return Response({
            'period': {
                'start_date': start_date,
                'end_date': end_date,
            },
            'summary': list(pharmacy_stats),
            'orders': order_details,
        })

"""
Billing module views.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum
from datetime import date
import requests
from .models import (
    ChargeItem, Bill, BillItem, Payment, Debt,
    ExternalPharmacy, DispensingOrder
)
from .serializers import (
    ChargeItemSerializer, BillSerializer, BillCreateSerializer,
    PaymentSerializer, DebtSerializer,
    ExternalPharmacySerializer, DispensingOrderSerializer, DispensingOrderCreateSerializer
)


class ChargeItemViewSet(viewsets.ModelViewSet):
    """收費項目管理"""
    queryset = ChargeItem.objects.all()
    serializer_class = ChargeItemSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['item_type', 'is_active']
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name']


class BillViewSet(viewsets.ModelViewSet):
    """帳單管理"""
    queryset = Bill.objects.select_related('registration', 'patient').prefetch_related('items')
    permission_classes = [IsAuthenticated]
    filterset_fields = ['patient', 'status', 'bill_date']
    search_fields = ['bill_number', 'patient__name', 'patient__chart_number']
    ordering_fields = ['bill_date', 'created_at']
    ordering = ['-bill_date', '-created_at']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BillCreateSerializer
        return BillSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        """付款"""
        bill = self.get_object()
        amount = request.data.get('amount')
        payment_method = request.data.get('payment_method')
        reference_number = request.data.get('reference_number', '')
        
        if not amount or not payment_method:
            return Response(
                {'error': 'amount and payment_method are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 建立付款記錄
        payment = Payment.objects.create(
            bill=bill,
            amount=amount,
            payment_method=payment_method,
            reference_number=reference_number,
            created_by=request.user
        )
        
        # 更新帳單
        bill.paid_amount += payment.amount
        bill.balance_due = bill.total_amount - bill.paid_amount
        
        if bill.balance_due <= 0:
            bill.status = Bill.Status.PAID
            bill.paid_at = timezone.now()
            bill.payment_method = payment_method
        elif bill.paid_amount > 0:
            bill.status = Bill.Status.PARTIAL
        
        bill.save()
        
        # 如果還有欠款，建立欠款記錄
        if bill.balance_due > 0:
            Debt.objects.update_or_create(
                bill=bill,
                defaults={
                    'patient': bill.patient,
                    'original_amount': bill.balance_due,
                    'remaining_amount': bill.balance_due,
                    'status': Debt.Status.OUTSTANDING
                }
            )
        
        serializer = BillSerializer(bill)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """退款"""
        bill = self.get_object()
        amount = request.data.get('amount')
        reason = request.data.get('reason', '')
        
        if not amount:
            return Response({'error': 'amount is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 檢查是否已扣庫
        has_dispensed = bill.registration.consultation.prescriptions.filter(is_dispensed=True).exists()
        if has_dispensed:
            return Response(
                {'error': '已配藥的帳單無法退款'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 建立負數付款記錄
        Payment.objects.create(
            bill=bill,
            amount=-amount,
            payment_method=Bill.PaymentMethod.OTHER,
            notes=f'退款: {reason}',
            created_by=request.user
        )
        
        # 更新帳單
        bill.paid_amount -= amount
        bill.balance_due = bill.total_amount - bill.paid_amount
        
        if bill.paid_amount <= 0:
            bill.status = Bill.Status.REFUNDED
        else:
            bill.status = Bill.Status.PARTIAL
        
        bill.save()
        
        # 可選：將退款金額存入病患帳戶
        store_to_account = request.data.get('store_to_account', False)
        if store_to_account:
            bill.patient.balance += amount
            bill.patient.save()
        
        serializer = BillSerializer(bill)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='credit-to-account')
    def credit_to_account(self, request, pk=None):
        """將已付款項轉存至病患帳戶"""
        bill = self.get_object()
        amount = request.data.get('amount')
        
        if not amount:
            return Response({'error': 'amount is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        amount = float(amount)
        if amount <= 0 or amount > bill.paid_amount:
            return Response(
                {'error': '金額必須大於 0 且不超過已付金額'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 將金額存入病患帳戶
        bill.patient.balance += amount
        bill.patient.save()
        
        # 建立負數付款記錄
        Payment.objects.create(
            bill=bill,
            amount=-amount,
            payment_method=Bill.PaymentMethod.OTHER,
            notes='轉存至病患帳戶',
            created_by=request.user
        )
        
        # 更新帳單
        bill.paid_amount -= amount
        bill.balance_due = bill.total_amount - bill.paid_amount
        if bill.paid_amount <= 0:
            bill.status = Bill.Status.PENDING
        elif bill.balance_due > 0:
            bill.status = Bill.Status.PARTIAL
        bill.save()
        
        serializer = BillSerializer(bill)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消帳單"""
        bill = self.get_object()
        
        if bill.status == Bill.Status.PAID:
            return Response(
                {'error': '已付款的帳單無法取消'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        bill.status = Bill.Status.CANCELLED
        bill.save()
        
        return Response({'status': 'cancelled'})


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """付款記錄（只讀）"""
    queryset = Payment.objects.select_related('bill', 'created_by')
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['bill', 'payment_method']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class DebtViewSet(viewsets.ModelViewSet):
    """欠款管理"""
    queryset = Debt.objects.select_related('patient', 'bill')
    serializer_class = DebtSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['patient', 'status']
    search_fields = ['patient__name', 'patient__chart_number']
    ordering_fields = ['created_at', 'remaining_amount']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        """清償欠款"""
        debt = self.get_object()
        amount = request.data.get('amount')
        payment_method = request.data.get('payment_method')
        
        if not amount or not payment_method:
            return Response(
                {'error': 'amount and payment_method are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 更新欠款
        debt.remaining_amount -= amount
        if debt.remaining_amount <= 0:
            debt.remaining_amount = 0
            debt.status = Debt.Status.CLEARED
        elif debt.remaining_amount < debt.original_amount:
            debt.status = Debt.Status.PARTIAL
        
        debt.save()
        
        # 更新帳單
        bill = debt.bill
        bill.paid_amount += amount
        bill.balance_due = bill.total_amount - bill.paid_amount
        if bill.balance_due <= 0:
            bill.status = Bill.Status.PAID
            bill.paid_at = timezone.now()
        bill.save()
        
        # 建立付款記錄
        Payment.objects.create(
            bill=bill,
            amount=amount,
            payment_method=payment_method,
            notes='欠款清償',
            created_by=request.user
        )
        
        serializer = DebtSerializer(debt)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_patient(self, request):
        """取得病患的欠款"""
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response({'error': 'patient_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        debts = Debt.objects.filter(
            patient_id=patient_id,
            status__in=[Debt.Status.OUTSTANDING, Debt.Status.PARTIAL]
        )
        
        total = debts.aggregate(total=Sum('remaining_amount'))['total'] or 0
        serializer = DebtSerializer(debts, many=True)
        
        return Response({
            'total_debt': total,
            'debts': serializer.data
        })


class ExternalPharmacyViewSet(viewsets.ModelViewSet):
    """外部配藥房管理"""
    queryset = ExternalPharmacy.objects.all()
    serializer_class = ExternalPharmacySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['pharmacy_type', 'is_active']
    search_fields = ['name']
    ordering_fields = ['name']


class DispensingOrderViewSet(viewsets.ModelViewSet):
    """派藥訂單管理"""
    queryset = DispensingOrder.objects.select_related('prescription', 'external_pharmacy')
    permission_classes = [IsAuthenticated]
    filterset_fields = ['external_pharmacy', 'status']
    search_fields = ['order_number', 'client_order_id', 'tracking_number']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action in ['create']:
            return DispensingOrderCreateSerializer
        return DispensingOrderSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """發送訂單至外部配藥房"""
        order = self.get_object()
        
        if order.status != DispensingOrder.Status.PENDING:
            return Response(
                {'error': '只有待發送的訂單可以發送'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pharmacy = order.external_pharmacy
        
        # 準備 API 請求
        prescription = order.prescription
        items = []
        for item in prescription.items.all():
            items.append({
                'sku': item.medicine.external_sku or item.medicine.code,
                'name': item.medicine.name,
                'quantity': float(item.dosage * prescription.total_doses),
                'unit': item.unit
            })
        
        payload = {
            'client_order_id': order.client_order_id,
            'recipient': {
                'name': order.recipient_name,
                'phone': order.recipient_phone,
                'address': order.recipient_address
            },
            'items': items,
            'doses': prescription.total_doses,
            'notes': order.notes
        }
        
        try:
            # 發送 API 請求
            response = requests.post(
                f"{pharmacy.api_endpoint}/orders",
                json=payload,
                headers={
                    'Authorization': f'Bearer {pharmacy.api_key}',
                    'Content-Type': 'application/json'
                },
                timeout=30
            )
            
            order.api_response = response.json()
            
            if response.status_code == 200:
                order.status = DispensingOrder.Status.SENT
                order.sent_at = timezone.now()
            else:
                order.status = DispensingOrder.Status.FAILED
                order.error_message = response.text
            
        except Exception as e:
            order.status = DispensingOrder.Status.FAILED
            order.error_message = str(e)
        
        order.save()
        
        serializer = DispensingOrderSerializer(order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消訂單"""
        order = self.get_object()
        
        if order.status in [DispensingOrder.Status.SHIPPED, DispensingOrder.Status.COMPLETED]:
            return Response(
                {'error': '已發貨或已完成的訂單無法取消'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = DispensingOrder.Status.CANCELLED
        order.save()
        
        return Response({'status': 'cancelled'})
    
    @action(detail=False, methods=['post'])
    def webhook(self, request):
        """接收外部配藥房的 Webhook 回調"""
        # 驗證 Webhook API Key
        api_key = request.headers.get('X-API-Key')
        client_order_id = request.data.get('client_order_id')
        
        try:
            order = DispensingOrder.objects.get(client_order_id=client_order_id)
        except DispensingOrder.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # 驗證 API Key
        if api_key != order.external_pharmacy.webhook_api_key:
            return Response({'error': 'Invalid API key'}, status=status.HTTP_403_FORBIDDEN)
        
        # 更新訂單狀態
        event_type = request.data.get('event_type')
        
        if event_type == 'order_confirmed':
            order.status = DispensingOrder.Status.CONFIRMED
        elif event_type == 'processing':
            order.status = DispensingOrder.Status.PROCESSING
        elif event_type == 'shipped':
            order.status = DispensingOrder.Status.SHIPPED
            order.tracking_company = request.data.get('tracking_company', '')
            order.tracking_number = request.data.get('tracking_number', '')
        elif event_type == 'delivered':
            order.status = DispensingOrder.Status.COMPLETED
            order.completed_at = timezone.now()
        
        order.save()
        
        return Response({'status': 'ok'})


class DailySummaryView(APIView):
    """每日結算摘要"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        target_date = request.query_params.get('date')
        if target_date:
            from datetime import datetime
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        else:
            target_date = date.today()
        
        # 當日帳單統計
        bills = Bill.objects.filter(bill_date=target_date)
        
        total_revenue = bills.filter(
            status__in=[Bill.Status.PAID, Bill.Status.PARTIAL]
        ).aggregate(total=Sum('paid_amount'))['total'] or 0
        
        total_bills = bills.count()
        paid_bills = bills.filter(status=Bill.Status.PAID).count()
        pending_bills = bills.filter(status=Bill.Status.PENDING).count()
        
        # 付款方式統計
        payments = Payment.objects.filter(created_at__date=target_date, amount__gt=0)
        payment_by_method = {}
        for method, label in Bill.PaymentMethod.choices:
            amount = payments.filter(payment_method=method).aggregate(total=Sum('amount'))['total'] or 0
            if amount > 0:
                payment_by_method[label] = float(amount)
        
        # 掛號統計
        from registration.models import Registration
        registrations = Registration.objects.filter(registration_date=target_date)
        total_registrations = registrations.count()
        completed_registrations = registrations.filter(status=Registration.Status.COMPLETED).count()
        
        return Response({
            'date': target_date,
            'revenue': {
                'total': float(total_revenue),
                'by_payment_method': payment_by_method
            },
            'bills': {
                'total': total_bills,
                'paid': paid_bills,
                'pending': pending_bills
            },
            'registrations': {
                'total': total_registrations,
                'completed': completed_registrations
            }
        })

"""
Registration module views.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import date
from .models import Appointment, Registration
from .serializers import (
    AppointmentSerializer, RegistrationSerializer,
    RegistrationCreateSerializer, QueueItemSerializer
)


class AppointmentViewSet(viewsets.ModelViewSet):
    """預約管理"""
    queryset = Appointment.objects.select_related('patient', 'doctor', 'room')
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['patient', 'doctor', 'appointment_date', 'status']
    search_fields = ['patient__name', 'patient__chart_number']
    ordering_fields = ['appointment_date', 'appointment_time']
    ordering = ['appointment_date', 'appointment_time']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """確認預約"""
        appointment = self.get_object()
        appointment.status = Appointment.Status.CONFIRMED
        appointment.save()
        return Response({'status': 'confirmed'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消預約"""
        appointment = self.get_object()
        appointment.status = Appointment.Status.CANCELLED
        appointment.save()
        return Response({'status': 'cancelled'})
    
    @action(detail=True, methods=['post'])
    def convert_to_registration(self, request, pk=None):
        """將預約轉為掛號"""
        appointment = self.get_object()
        
        # 檢查是否已經有關聯的掛號
        if hasattr(appointment, 'registration'):
            return Response(
                {'error': '此預約已轉為掛號'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 計算候診號碼
        last_queue = Registration.objects.filter(
            registration_date=appointment.appointment_date,
            doctor=appointment.doctor
        ).order_by('-queue_number').first()
        queue_number = (last_queue.queue_number + 1) if last_queue else 1
        
        # 判斷是否為初診
        has_previous = Registration.objects.filter(
            patient=appointment.patient,
            status=Registration.Status.COMPLETED
        ).exists()
        visit_type = Registration.VisitType.FOLLOW_UP if has_previous else Registration.VisitType.FIRST_VISIT
        
        # 建立掛號
        registration = Registration.objects.create(
            patient=appointment.patient,
            doctor=appointment.doctor,
            room=appointment.room,
            appointment=appointment,
            queue_number=queue_number,
            visit_type=visit_type,
            registration_date=appointment.appointment_date,
            created_by=request.user
        )
        
        # 更新預約狀態
        appointment.status = Appointment.Status.COMPLETED
        appointment.save()
        
        serializer = RegistrationSerializer(registration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RegistrationViewSet(viewsets.ModelViewSet):
    """掛號管理"""
    queryset = Registration.objects.select_related('patient', 'doctor', 'room')
    permission_classes = [IsAuthenticated]
    filterset_fields = ['patient', 'doctor', 'registration_date', 'status', 'visit_type']
    search_fields = ['registration_number', 'patient__name', 'patient__chart_number']
    ordering_fields = ['registration_date', 'queue_number']
    ordering = ['registration_date', 'queue_number']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RegistrationCreateSerializer
        return RegistrationSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        """病患報到"""
        registration = self.get_object()
        registration.check_in_time = timezone.now()
        registration.status = Registration.Status.WAITING
        registration.save()
        return Response({'status': 'checked_in', 'check_in_time': registration.check_in_time})
    
    @action(detail=True, methods=['post'])
    def start_consultation(self, request, pk=None):
        """開始看診"""
        registration = self.get_object()
        registration.consultation_start_time = timezone.now()
        registration.status = Registration.Status.IN_CONSULTATION
        registration.save()
        return Response({'status': 'in_consultation'})
    
    @action(detail=True, methods=['post'])
    def end_consultation(self, request, pk=None):
        """結束看診並自動產生帳單"""
        registration = self.get_object()
        registration.consultation_end_time = timezone.now()
        registration.status = Registration.Status.COMPLETED
        registration.save()
        
        # 自動產生帳單
        from billing.models import Bill, BillItem, ChargeItem
        from consultation.models import Consultation, Prescription
        from datetime import date
        
        # 檢查是否已有帳單
        existing_bill = Bill.objects.filter(registration=registration).first()
        if not existing_bill:
            # 計算費用
            consultation_fee = 300  # 預設診金
            medicine_fee = 0
            
            # 取得診療記錄和處方
            consultation = Consultation.objects.filter(registration=registration).first()
            if consultation:
                prescriptions = Prescription.objects.filter(consultation=consultation)
                for prescription in prescriptions:
                    medicine_fee += float(prescription.medicine_fee or 0)
            
            total_amount = consultation_fee + medicine_fee
            
            # 建立帳單
            bill = Bill.objects.create(
                registration=registration,
                patient=registration.patient,
                bill_date=date.today(),
                subtotal=total_amount,
                total_amount=total_amount,
                paid_amount=0,
                balance_due=total_amount,
                status=Bill.Status.PENDING,
                created_by=request.user
            )
            
            # 建立帳單項目 - 診金
            BillItem.objects.create(
                bill=bill,
                description='診金',
                quantity=1,
                unit_price=consultation_fee,
                subtotal=consultation_fee
            )
            
            # 如果有藥費，建立藥費項目
            if medicine_fee > 0:
                BillItem.objects.create(
                    bill=bill,
                    description='藥費',
                    quantity=1,
                    unit_price=medicine_fee,
                    subtotal=medicine_fee
                )
        
        return Response({'status': 'completed'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消掛號"""
        registration = self.get_object()
        registration.status = Registration.Status.CANCELLED
        registration.save()
        return Response({'status': 'cancelled'})
    
    @action(detail=True, methods=['post'])
    def no_show(self, request, pk=None):
        """標記過號"""
        registration = self.get_object()
        registration.status = Registration.Status.NO_SHOW
        registration.save()
        return Response({'status': 'no_show'})


class TodayQueueView(APIView):
    """今日候診列表"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        today = date.today()
        doctor_id = request.query_params.get('doctor')
        room_id = request.query_params.get('room')
        
        queryset = Registration.objects.filter(
            registration_date=today
        ).select_related('patient').order_by('queue_number')
        
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        
        # 分組返回
        waiting = queryset.filter(status=Registration.Status.WAITING)
        in_consultation = queryset.filter(status=Registration.Status.IN_CONSULTATION)
        completed = queryset.filter(status=Registration.Status.COMPLETED)
        
        return Response({
            'waiting': QueueItemSerializer(waiting, many=True).data,
            'in_consultation': QueueItemSerializer(in_consultation, many=True).data,
            'completed': QueueItemSerializer(completed, many=True).data,
            'summary': {
                'total': queryset.count(),
                'waiting': waiting.count(),
                'in_consultation': in_consultation.count(),
                'completed': completed.count(),
            }
        })

"""
Consultation module views.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from .models import (
    DiagnosticTerm, Consultation, Prescription, PrescriptionItem,
    ExperienceFormula, ExperienceFormulaItem, Certificate
)
from .serializers import (
    DiagnosticTermSerializer, ConsultationSerializer, ConsultationListSerializer,
    PrescriptionSerializer, PrescriptionCreateSerializer,
    ExperienceFormulaSerializer, ExperienceFormulaCreateSerializer,
    CertificateSerializer
)


class DiagnosticTermViewSet(viewsets.ModelViewSet):
    """辨證詞庫管理"""
    queryset = DiagnosticTerm.objects.all()
    serializer_class = DiagnosticTermSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['category', 'is_active']
    search_fields = ['code', 'name']
    ordering_fields = ['category', 'name']
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """按類別分組返回"""
        category = request.query_params.get('category')
        if category:
            terms = DiagnosticTerm.objects.filter(category=category, is_active=True)
        else:
            terms = DiagnosticTerm.objects.filter(is_active=True)
        
        serializer = DiagnosticTermSerializer(terms, many=True)
        return Response(serializer.data)


class ConsultationViewSet(viewsets.ModelViewSet):
    """診療記錄管理"""
    queryset = Consultation.objects.select_related(
        'registration__patient', 'doctor'
    ).prefetch_related('prescriptions__items')
    permission_classes = [IsAuthenticated]
    filterset_fields = ['doctor', 'registration__patient']
    search_fields = ['registration__patient__name', 'tcm_diagnosis']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ConsultationListSerializer
        return ConsultationSerializer
    
    def perform_create(self, serializer):
        """建立診療記錄時自動設定醫師為當前使用者"""
        serializer.save(doctor=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_patient(self, request):
        """取得病患的診療歷史"""
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response({'error': 'patient_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        consultations = Consultation.objects.filter(
            registration__patient_id=patient_id
        ).order_by('-created_at')[:20]
        
        serializer = ConsultationListSerializer(consultations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def copy_from_previous(self, request, pk=None):
        """從上次診療複製資料"""
        consultation = self.get_object()
        patient = consultation.registration.patient
        
        # 找到上一次的診療記錄
        previous = Consultation.objects.filter(
            registration__patient=patient,
            created_at__lt=consultation.created_at
        ).order_by('-created_at').first()
        
        if not previous:
            return Response({'error': '找不到上次診療記錄'}, status=status.HTTP_404_NOT_FOUND)
        
        # 複製四診資料
        fields_to_copy = [
            'chief_complaint', 'present_illness', 'inspection',
            'tongue_appearance', 'pulse', 'tcm_diagnosis',
            'syndrome_differentiation', 'treatment_principle'
        ]
        
        for field in fields_to_copy:
            setattr(consultation, field, getattr(previous, field))
        
        consultation.save()
        serializer = ConsultationSerializer(consultation)
        return Response(serializer.data)


class PrescriptionViewSet(viewsets.ModelViewSet):
    """處方管理"""
    queryset = Prescription.objects.select_related(
        'consultation__registration__patient', 'external_pharmacy'
    ).prefetch_related('items__medicine')
    permission_classes = [IsAuthenticated]
    filterset_fields = ['consultation', 'dispensing_method', 'is_dispensed']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PrescriptionCreateSerializer
        return PrescriptionSerializer
    
    def update(self, request, *args, **kwargs):
        """更新處方（僅限開方醫師且未配藥）"""
        instance = self.get_object()
        
        # 檢查是否已配藥
        if instance.is_dispensed:
            return Response(
                {'error': '處方已配藥，無法修改'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 檢查是否為開方醫師
        if instance.consultation.doctor != request.user:
            return Response(
                {'error': '只有開方醫師可以修改處方'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 記錄修改前的資料
        before_data = PrescriptionSerializer(instance).data
        
        response = super().update(request, *args, **kwargs)
        
        # 記錄稽核日誌
        instance.refresh_from_db()
        if instance.audit_log is None:
            instance.audit_log = []
        instance.audit_log.append({
            'timestamp': timezone.now().isoformat(),
            'user': request.user.username,
            'before': before_data,
            'after': PrescriptionSerializer(instance).data
        })
        instance.save()
        
        return response
    
    @action(detail=True, methods=['post'])
    def dispense(self, request, pk=None):
        """標記處方已配藥"""
        prescription = self.get_object()
        
        if prescription.is_dispensed:
            return Response({'error': '處方已配藥'}, status=status.HTTP_400_BAD_REQUEST)
        
        prescription.is_dispensed = True
        prescription.dispensed_at = timezone.now()
        prescription.save()
        
        # 扣減庫存
        from inventory.models import Inventory, InventoryTransaction
        
        for item in prescription.items.all():
            try:
                inventory = Inventory.objects.get(medicine=item.medicine)
                before_qty = inventory.quantity
                inventory.quantity -= item.dosage * prescription.total_doses
                inventory.save()
                
                # 記錄庫存異動
                InventoryTransaction.objects.create(
                    medicine=item.medicine,
                    transaction_type=InventoryTransaction.TransactionType.DISPENSE,
                    quantity=-(item.dosage * prescription.total_doses),
                    before_quantity=before_qty,
                    after_quantity=inventory.quantity,
                    reference_number=prescription.prescription_number,
                    created_by=request.user
                )
            except Inventory.DoesNotExist:
                pass
        
        return Response({'status': 'dispensed'})
    
    @action(detail=False, methods=['post'])
    def check_stock(self, request):
        """檢查處方藥品庫存"""
        items = request.data.get('items', [])
        
        from inventory.models import Inventory, Medicine
        
        results = []
        has_insufficient = False
        
        for item in items:
            medicine_id = item.get('medicine_id')
            required_qty = float(item.get('quantity', 0))
            
            try:
                medicine = Medicine.objects.get(id=medicine_id)
                try:
                    inventory = Inventory.objects.get(medicine=medicine)
                    available = float(inventory.quantity)
                except Inventory.DoesNotExist:
                    available = 0
                
                is_sufficient = available >= required_qty
                if not is_sufficient:
                    has_insufficient = True
                
                results.append({
                    'medicine_id': medicine_id,
                    'medicine_name': medicine.name,
                    'required': required_qty,
                    'available': available,
                    'is_sufficient': is_sufficient,
                    'safety_stock': float(medicine.safety_stock) if hasattr(medicine, 'safety_stock') else 0
                })
            except Medicine.DoesNotExist:
                results.append({
                    'medicine_id': medicine_id,
                    'error': '藥品不存在'
                })
        
        return Response({
            'all_sufficient': not has_insufficient,
            'items': results
        })
    
    @action(detail=True, methods=['post'])
    def apply_experience_formula(self, request, pk=None):
        """套用經驗方"""
        prescription = self.get_object()
        formula_id = request.data.get('formula_id')
        
        if not formula_id:
            return Response({'error': 'formula_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            formula = ExperienceFormula.objects.get(id=formula_id)
        except ExperienceFormula.DoesNotExist:
            return Response({'error': '經驗方不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        # 複製經驗方項目到處方
        for formula_item in formula.items.all():
            PrescriptionItem.objects.create(
                prescription=prescription,
                medicine=formula_item.medicine,
                dosage=formula_item.dosage,
                unit=formula_item.unit,
                decoction_method=formula_item.decoction_method,
                unit_price=formula_item.medicine.selling_price,
                notes=formula_item.notes
            )
        
        # 更新處方資訊
        prescription.name = formula.name
        prescription.usage_instruction = formula.usage_instruction
        prescription.save()
        
        # 重新計算藥費
        total_fee = sum(item.subtotal for item in prescription.items.all())
        prescription.medicine_fee = total_fee
        prescription.save()
        
        serializer = PrescriptionSerializer(prescription)
        return Response(serializer.data)


class ExperienceFormulaViewSet(viewsets.ModelViewSet):
    """經驗方管理"""
    queryset = ExperienceFormula.objects.select_related('doctor').prefetch_related('items__medicine')
    permission_classes = [IsAuthenticated]
    filterset_fields = ['doctor', 'category', 'is_public']
    search_fields = ['name', 'indication']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ExperienceFormulaCreateSerializer
        return ExperienceFormulaSerializer
    
    def get_queryset(self):
        # 返回自己的經驗方和公開的經驗方
        user = self.request.user
        return ExperienceFormula.objects.filter(
            Q(doctor=user) | Q(is_public=True)
        )
    
    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user)
    
    @action(detail=True, methods=['post'])
    def save_from_prescription(self, request, pk=None):
        """從處方儲存為經驗方"""
        prescription_id = request.data.get('prescription_id')
        name = request.data.get('name')
        
        if not prescription_id or not name:
            return Response(
                {'error': 'prescription_id and name are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            prescription = Prescription.objects.get(id=prescription_id)
        except Prescription.DoesNotExist:
            return Response({'error': '處方不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        # 建立經驗方
        formula = ExperienceFormula.objects.create(
            doctor=request.user,
            name=name,
            usage_instruction=prescription.usage_instruction
        )
        
        # 複製處方項目
        for item in prescription.items.all():
            ExperienceFormulaItem.objects.create(
                formula=formula,
                medicine=item.medicine,
                dosage=item.dosage,
                unit=item.unit,
                decoction_method=item.decoction_method
            )
        
        serializer = ExperienceFormulaSerializer(formula)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CertificateViewSet(viewsets.ModelViewSet):
    """證明書管理"""
    queryset = Certificate.objects.select_related('consultation__registration__patient')
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['consultation', 'certificate_type']
    search_fields = ['certificate_number', 'consultation__registration__patient__name']
    ordering_fields = ['created_at', 'issue_date']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        # 自動生成證明書編號
        from datetime import date
        today = date.today()
        prefix = f"C{today.strftime('%Y%m%d')}"
        last_cert = Certificate.objects.filter(
            certificate_number__startswith=prefix
        ).order_by('-certificate_number').first()
        
        if last_cert:
            last_num = int(last_cert.certificate_number[-4:])
            new_num = last_num + 1
        else:
            new_num = 1
        
        serializer.save(
            certificate_number=f"{prefix}{new_num:04d}",
            created_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def print(self, request, pk=None):
        """記錄列印"""
        certificate = self.get_object()
        certificate.print_count += 1
        certificate.last_printed_at = timezone.now()
        certificate.save()
        
        return Response({
            'status': 'printed',
            'print_count': certificate.print_count
        })

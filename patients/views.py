"""
Patients module views.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Patient, PatientImage
from .serializers import PatientSerializer, PatientListSerializer, PatientImageSerializer


class PatientViewSet(viewsets.ModelViewSet):
    """病患管理"""
    queryset = Patient.objects.all()
    permission_classes = [IsAuthenticated]
    filterset_fields = ['gender', 'is_active']
    search_fields = ['chart_number', 'name', 'phone', 'mobile', 'id_card_number']
    ordering_fields = ['chart_number', 'name', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PatientListSerializer
        return PatientSerializer
    
    def perform_create(self, serializer):
        # 自動生成病歷號碼
        last_patient = Patient.objects.order_by('-chart_number').first()
        if last_patient and last_patient.chart_number.isdigit():
            new_number = int(last_patient.chart_number) + 1
        else:
            new_number = 1
        
        serializer.save(
            chart_number=f"{new_number:06d}",
            created_by=self.request.user
        )
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """取得病患的就診歷史"""
        patient = self.get_object()
        registrations = patient.registrations.select_related(
            'doctor', 'room'
        ).order_by('-registration_date')[:20]
        
        history = []
        for reg in registrations:
            history.append({
                'id': reg.id,
                'registration_number': reg.registration_number,
                'date': reg.registration_date,
                'doctor': reg.doctor.get_full_name(),
                'status': reg.get_status_display(),
                'visit_type': reg.get_visit_type_display(),
            })
        
        return Response(history)
    
    @action(detail=True, methods=['get', 'post'])
    def images(self, request, pk=None):
        """病患影像管理"""
        patient = self.get_object()
        
        if request.method == 'GET':
            images = patient.images.all()
            serializer = PatientImageSerializer(images, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = PatientImageSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(patient=patient, created_by=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """快速搜尋病患"""
        query = request.query_params.get('q', '')
        if len(query) < 2:
            return Response([])
        
        patients = Patient.objects.filter(
            Q(chart_number__icontains=query) |
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(mobile__icontains=query)
        )[:10]
        
        serializer = PatientListSerializer(patients, many=True)
        return Response(serializer.data)

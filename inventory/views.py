"""
Inventory module views.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, F
from django.utils import timezone
from .models import (
    MedicineCategory, Supplier, Medicine, Inventory,
    InventoryTransaction, PurchaseOrder, PurchaseOrderItem, CompoundFormula
)
from .serializers import (
    MedicineCategorySerializer, SupplierSerializer,
    MedicineSerializer, MedicineListSerializer,
    InventorySerializer, InventoryTransactionSerializer,
    PurchaseOrderSerializer, PurchaseOrderCreateSerializer,
    CompoundFormulaSerializer
)


class MedicineCategoryViewSet(viewsets.ModelViewSet):
    """藥品分類管理"""
    queryset = MedicineCategory.objects.all()
    serializer_class = MedicineCategorySerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name', 'code']
    ordering_fields = ['code', 'name']


class SupplierViewSet(viewsets.ModelViewSet):
    """供應商管理"""
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'contact_person']
    ordering_fields = ['name', 'code']


class MedicineViewSet(viewsets.ModelViewSet):
    """藥品管理"""
    queryset = Medicine.objects.select_related('category', 'supplier')
    permission_classes = [IsAuthenticated]
    filterset_fields = ['medicine_type', 'category', 'supplier', 'is_active']
    search_fields = ['code', 'name', 'pinyin', 'english_name']
    ordering_fields = ['code', 'name', 'created_at']
    ordering = ['code']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MedicineListSerializer
        return MedicineSerializer
    
    def perform_create(self, serializer):
        medicine = serializer.save()
        # 自動建立庫存記錄
        Inventory.objects.create(medicine=medicine, quantity=0)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """快速搜尋藥品"""
        query = request.query_params.get('q', '')
        if len(query) < 1:
            return Response([])
        
        medicines = Medicine.objects.filter(
            Q(code__icontains=query) |
            Q(name__icontains=query) |
            Q(pinyin__icontains=query)
        ).filter(is_active=True)[:20]
        
        serializer = MedicineListSerializer(medicines, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """取得藥品的庫存異動記錄"""
        medicine = self.get_object()
        transactions = medicine.transactions.order_by('-created_at')[:50]
        serializer = InventoryTransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class InventoryViewSet(viewsets.ModelViewSet):
    """庫存管理"""
    queryset = Inventory.objects.select_related('medicine')
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['medicine']
    ordering_fields = ['quantity', 'last_updated']
    
    @action(detail=True, methods=['post'])
    def adjust(self, request, pk=None):
        """盤點調整"""
        inventory = self.get_object()
        new_quantity = request.data.get('quantity')
        reason = request.data.get('reason', '')
        
        if new_quantity is None:
            return Response({'error': 'quantity is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        before_qty = inventory.quantity
        inventory.quantity = new_quantity
        inventory.save()
        
        # 記錄異動
        InventoryTransaction.objects.create(
            medicine=inventory.medicine,
            transaction_type=InventoryTransaction.TransactionType.ADJUSTMENT,
            quantity=new_quantity - before_qty,
            before_quantity=before_qty,
            after_quantity=new_quantity,
            notes=reason,
            created_by=request.user
        )
        
        serializer = InventorySerializer(inventory)
        return Response(serializer.data)


class InventoryTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """庫存異動記錄（只讀）"""
    queryset = InventoryTransaction.objects.select_related('medicine', 'created_by')
    serializer_class = InventoryTransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['medicine', 'transaction_type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """進貨單管理"""
    queryset = PurchaseOrder.objects.select_related('supplier').prefetch_related('items__medicine')
    permission_classes = [IsAuthenticated]
    filterset_fields = ['supplier', 'status']
    search_fields = ['order_number']
    ordering_fields = ['order_date', 'created_at']
    ordering = ['-order_date']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PurchaseOrderCreateSerializer
        return PurchaseOrderSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """提交進貨單"""
        order = self.get_object()
        order.status = PurchaseOrder.Status.SUBMITTED
        order.save()
        return Response({'status': 'submitted'})
    
    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        """收貨"""
        order = self.get_object()
        
        # 更新庫存
        for item in order.items.all():
            try:
                inventory = Inventory.objects.get(medicine=item.medicine)
            except Inventory.DoesNotExist:
                inventory = Inventory.objects.create(medicine=item.medicine, quantity=0)
            
            before_qty = inventory.quantity
            inventory.quantity += item.quantity
            inventory.save()
            
            # 記錄異動
            InventoryTransaction.objects.create(
                medicine=item.medicine,
                transaction_type=InventoryTransaction.TransactionType.PURCHASE,
                quantity=item.quantity,
                before_quantity=before_qty,
                after_quantity=inventory.quantity,
                unit_cost=item.unit_price,
                reference_number=order.order_number,
                created_by=request.user
            )
            
            # 更新收貨數量
            item.received_quantity = item.quantity
            item.save()
        
        order.status = PurchaseOrder.Status.RECEIVED
        order.received_date = timezone.now().date()
        order.save()
        
        return Response({'status': 'received'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消進貨單"""
        order = self.get_object()
        if order.status == PurchaseOrder.Status.RECEIVED:
            return Response(
                {'error': '已收貨的進貨單無法取消'},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = PurchaseOrder.Status.CANCELLED
        order.save()
        return Response({'status': 'cancelled'})


class CompoundFormulaViewSet(viewsets.ModelViewSet):
    """複方成份管理"""
    queryset = CompoundFormula.objects.select_related('compound_medicine', 'ingredient_medicine')
    serializer_class = CompoundFormulaSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['compound_medicine']


class LowStockView(APIView):
    """低庫存警報"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        low_stock_items = Inventory.objects.filter(
            quantity__lt=F('medicine__safety_stock')
        ).select_related('medicine')
        
        serializer = InventorySerializer(low_stock_items, many=True)
        return Response({
            'count': low_stock_items.count(),
            'items': serializer.data
        })

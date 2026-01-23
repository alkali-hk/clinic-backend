"""
Inventory module URL configuration.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'medicines', views.MedicineViewSet)
router.register(r'categories', views.MedicineCategoryViewSet)
router.register(r'suppliers', views.SupplierViewSet)
router.register(r'inventory', views.InventoryViewSet)
router.register(r'transactions', views.InventoryTransactionViewSet)
router.register(r'purchase-orders', views.PurchaseOrderViewSet)
router.register(r'compound-formulas', views.CompoundFormulaViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('low-stock/', views.LowStockView.as_view(), name='low-stock'),
]

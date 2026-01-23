"""
Billing module URL configuration.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'charge-items', views.ChargeItemViewSet)
router.register(r'bills', views.BillViewSet)
router.register(r'payments', views.PaymentViewSet)
router.register(r'debts', views.DebtViewSet)
router.register(r'external-pharmacies', views.ExternalPharmacyViewSet)
router.register(r'dispensing-orders', views.DispensingOrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('daily-summary/', views.DailySummaryView.as_view(), name='daily-summary'),
]

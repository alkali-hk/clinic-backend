"""
Reports module URL configuration.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'templates', views.ReportTemplateViewSet)
router.register(r'generated', views.GeneratedReportViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('daily-summary/', views.DailySummaryReportView.as_view(), name='daily-summary-report'),
    path('monthly-summary/', views.MonthlySummaryReportView.as_view(), name='monthly-summary-report'),
    path('doctor-workload/', views.DoctorWorkloadReportView.as_view(), name='doctor-workload-report'),
    path('medicine-usage/', views.MedicineUsageReportView.as_view(), name='medicine-usage-report'),
    path('external-pharmacy-reconciliation/', views.ExternalPharmacyReconciliationView.as_view(), name='external-pharmacy-reconciliation'),
]

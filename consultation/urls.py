"""
Consultation module URL configuration.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'consultations', views.ConsultationViewSet)
router.register(r'prescriptions', views.PrescriptionViewSet)
router.register(r'experience-formulas', views.ExperienceFormulaViewSet)
router.register(r'certificates', views.CertificateViewSet)
router.register(r'diagnostic-terms', views.DiagnosticTermViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

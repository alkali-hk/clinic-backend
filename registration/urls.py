"""
Registration module URL configuration.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'appointments', views.AppointmentViewSet)
router.register(r'registrations', views.RegistrationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('today/', views.TodayQueueView.as_view(), name='today-queue'),
    path('queue/', views.TodayQueueView.as_view(), name='queue'),
]

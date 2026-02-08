"""
URL configuration for Clinic Management System.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from core.auth_views import LoginView, LogoutView
from core.views import InitDataView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # JWT Authentication
    path('api/v1/auth/login/', LoginView.as_view(), name='login'),
    path('api/v1/auth/logout/', LogoutView.as_view(), name='logout'),
    path('api/v1/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Init data endpoint
    path('api/v1/init-data/', InitDataView.as_view(), name='init-data'),
    
    # API endpoints
    path('api/v1/core/', include('core.urls')),
    path('api/v1/patients/', include('patients.urls')),
    path('api/v1/registration/', include('registration.urls')),
    path('api/v1/consultation/', include('consultation.urls')),
    path('api/v1/billing/', include('billing.urls')),
    path('api/v1/inventory/', include('inventory.urls')),
    path('api/v1/reports/', include('reports.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

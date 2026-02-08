"""
Core module views.
"""

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.contrib.auth import get_user_model
from django.core.management import call_command
import os
import io
from .models import ClinicSettings, ClinicRoom, Schedule
from .serializers import (
    UserSerializer, UserCreateSerializer,
    ClinicSettingsSerializer, ClinicRoomSerializer, ScheduleSerializer
)

User = get_user_model()


class CurrentUserView(APIView):
    """當前使用者資訊"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """使用者管理"""
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    filterset_fields = ['role', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['username', 'date_joined']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def get_queryset(self):
        # 非管理員只能看到自己
        if not self.request.user.is_admin_user:
            return User.objects.filter(id=self.request.user.id)
        return User.objects.all()


class ClinicSettingsViewSet(viewsets.ModelViewSet):
    """診所設定管理"""
    queryset = ClinicSettings.objects.all()
    serializer_class = ClinicSettingsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # 只返回第一筆設定（單一診所）
        return ClinicSettings.objects.all()[:1]


class ClinicRoomViewSet(viewsets.ModelViewSet):
    """診間管理"""
    queryset = ClinicRoom.objects.all()
    serializer_class = ClinicRoomSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code']
    ordering_fields = ['code', 'name']


class ScheduleViewSet(viewsets.ModelViewSet):
    """排班管理"""
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['doctor', 'room', 'day_of_week', 'period', 'is_active']
    ordering_fields = ['day_of_week', 'period']


class InitDataView(APIView):
    """初始化數據端點 - 用於生產環境初始化"""
    permission_classes = [AllowAny]

    def post(self, request):
        secret = request.data.get('secret', '')
        init_secret = os.environ.get('INIT_SECRET', 'clinic-init-2024')
        if secret != init_secret:
            return Response({'detail': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        output = io.StringIO()
        try:
            call_command('init_data', stdout=output)
            return Response({'detail': 'OK', 'output': output.getvalue()})
        except Exception as e:
            return Response({'detail': str(e), 'output': output.getvalue()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

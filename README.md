# 診所管理系統 - 後端 (Clinic Management System Backend)

Django REST API 後端，用於診所管理系統。

## 技術棧

- Django 5.0
- Django REST Framework
- PostgreSQL
- JWT Authentication (SimpleJWT)

## 功能模組

- 使用者認證與授權
- 病患管理
- 掛號作業
- 診療工作台
- 收款作業
- 庫存管理
- 報表系統

## 部署

### 環境變數

```
DATABASE_URL=postgresql://user:password@host:5432/dbname
DJANGO_SECRET_KEY=your-secret-key
DEBUG=False
FRONTEND_URL=https://your-frontend-url.com
```

### 安裝

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## API 文檔

API 端點基於 RESTful 設計，主要包括：

- `/api/auth/` - 認證相關
- `/api/patients/` - 病患管理
- `/api/registrations/` - 掛號作業
- `/api/consultations/` - 診療記錄
- `/api/billing/` - 收款作業
- `/api/inventory/` - 庫存管理
- `/api/reports/` - 報表系統

## 授權

Private - 僅供內部使用

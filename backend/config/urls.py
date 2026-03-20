from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from crm.views import AttachmentViewSet, DataSourceViewSet, RecordViewSet, UserProfileViewSet

router = DefaultRouter()
router.register(r'profile', UserProfileViewSet, basename='profile')
router.register(r'datasources', DataSourceViewSet, basename='datasource')
router.register(r'records', RecordViewSet, basename='record')
router.register(r'attachments', AttachmentViewSet, basename='attachment')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

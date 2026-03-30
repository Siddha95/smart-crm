from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from crm.views import AttachmentViewSet, DataSourceViewSet, MapPinViewSet, NoteViewSet, RecordCommentViewSet, RecordViewSet, StageTemplateViewSet, UserProfileViewSet

router = DefaultRouter()
router.register(r'profile', UserProfileViewSet, basename='profile')
router.register(r'datasources', DataSourceViewSet, basename='datasource')
router.register(r'records', RecordViewSet, basename='record')
router.register(r'attachments', AttachmentViewSet, basename='attachment')
router.register(r'comments', RecordCommentViewSet, basename='comment')
router.register(r'notes', NoteViewSet, basename='note')
router.register(r'stage-templates', StageTemplateViewSet, basename='stage-template')
router.register(r'map-pins', MapPinViewSet, basename='map-pin')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

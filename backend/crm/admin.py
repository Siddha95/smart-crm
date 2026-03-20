from django.contrib import admin

from crm.models import Attachment, DataSource, Record, RecordHistory, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'personal_api_key']


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'label', 'owner', 'created_at']
    search_fields = ['name', 'label', 'owner__username']
    list_filter = ['owner']


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'data_source', 'is_active', 'created_at', 'updated_at']
    list_filter = ['data_source', 'is_active']


@admin.register(RecordHistory)
class RecordHistoryAdmin(admin.ModelAdmin):
    list_display = ['record', 'field_changed', 'changed_by', 'changed_at']
    list_filter = ['changed_by']


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'record', 'file_type', 'label', 'uploaded_by', 'uploaded_at']
    list_filter = ['file_type']

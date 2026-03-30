from rest_framework import serializers

from crm.models import Attachment, DataSource, MapPin, Note, Record, RecordComment, RecordHistory, StageTemplate, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    has_api_key = serializers.SerializerMethodField(read_only=True)

    def get_has_api_key(self, obj):
        return bool(obj.personal_api_key)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'personal_api_key', 'has_api_key', 'ai_context']
        extra_kwargs = {'personal_api_key': {'write_only': True}}


class DataSourceSerializer(serializers.ModelSerializer):
    record_count = serializers.IntegerField(source='records.count', read_only=True)

    class Meta:
        model = DataSource
        fields = ['id', 'name', 'label', 'columns', 'stages', 'source_file', 'created_at', 'record_count']
        read_only_fields = ['created_at']


class AttachmentSerializer(serializers.ModelSerializer):
    filename = serializers.CharField(read_only=True)
    file_url = serializers.SerializerMethodField()
    uploaded_by = serializers.StringRelatedField(read_only=True)

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else None

    class Meta:
        model = Attachment
        fields = ['id', 'record', 'file', 'file_type', 'label', 'filename', 'file_url', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['uploaded_at']


class RecordHistorySerializer(serializers.ModelSerializer):
    changed_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = RecordHistory
        fields = ['id', 'changed_at', 'changed_by', 'field_changed', 'old_value', 'new_value']
        read_only_fields = ['changed_at']


class RecordCommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = RecordComment
        fields = ['id', 'record', 'user', 'text', 'created_at']
        read_only_fields = ['created_at']


class StageTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StageTemplate
        fields = ['id', 'name', 'stages']


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'title', 'content', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class MapPinSerializer(serializers.ModelSerializer):
    record_data = serializers.SerializerMethodField()
    datasource_label = serializers.SerializerMethodField()
    columns = serializers.SerializerMethodField()

    def get_record_data(self, obj):
        return obj.record.data

    def get_datasource_label(self, obj):
        return obj.record.data_source.label

    def get_columns(self, obj):
        return obj.record.data_source.columns

    def validate_record(self, record):
        request = self.context.get('request')
        if record.data_source.owner != request.user:
            raise serializers.ValidationError('Record non trovato.')
        return record

    class Meta:
        model = MapPin
        fields = ['id', 'record', 'lat', 'lng', 'color', 'created_at', 'record_data', 'datasource_label', 'columns']
        read_only_fields = ['created_at']


class RecordSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)
    history = RecordHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Record
        fields = [
            'id', 'data_source', 'data', 'is_active', 'is_favorite', 'stage', 'position',
            'created_at', 'updated_at', 'attachments', 'history',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_data(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError('I dati del record devono essere un oggetto JSON.')
        return value

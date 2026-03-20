from rest_framework import serializers

from crm.models import Attachment, DataSource, Record, RecordHistory, UserProfile

# Serializers per API REST
class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'personal_api_key']
        extra_kwargs = {'personal_api_key': {'write_only': True}}

# Serializer per DataSource, Record, RecordHistory e Attachment
class DataSourceSerializer(serializers.ModelSerializer):
    record_count = serializers.IntegerField(source='records.count', read_only=True)

    class Meta:
        model = DataSource
        fields = ['id', 'name', 'label', 'columns', 'created_at', 'record_count']
        read_only_fields = ['created_at']

# Serializer per Record e RecordHistory
class AttachmentSerializer(serializers.ModelSerializer):
    filename = serializers.CharField(read_only=True)
    file_url = serializers.CharField(read_only=True)
    uploaded_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Attachment
        fields = ['id', 'file', 'file_type', 'label', 'filename', 'file_url', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['uploaded_at']

# Serializer per Record e RecordHistory
class RecordHistorySerializer(serializers.ModelSerializer):
    changed_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = RecordHistory
        fields = ['id', 'changed_at', 'changed_by', 'field_changed', 'old_value', 'new_value']
        read_only_fields = ['changed_at']

# Serializer per Record, include attachment e history
class RecordSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)
    history = RecordHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Record
        fields = ['id', 'data_source', 'data', 'is_active', 'created_at', 'updated_at', 'attachments', 'history']
        read_only_fields = ['created_at', 'updated_at']

    def validate_data(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError('I dati del record devono essere un oggetto JSON.')
        return value

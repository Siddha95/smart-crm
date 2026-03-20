import os
import tempfile

from rest_framework import viewsets, status, parsers
from rest_framework.decorators import action
from rest_framework.response import Response

from crm.models import Attachment, DataSource, Record, RecordHistory, UserProfile
from crm.serializers import (
    AttachmentSerializer,
    DataSourceSerializer,
    RecordHistorySerializer,
    RecordSerializer,
    UserProfileSerializer,
)
from crm.services.excel_import import import_file
from crm.services.embedding import get_embedding_provider


class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user).select_related('user')


class DataSourceViewSet(viewsets.ModelViewSet):
    serializer_class = DataSourceSerializer

    def get_queryset(self):
        return DataSource.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=['post'], parser_classes=[parsers.MultiPartParser])
    def upload(self, request):
        """Carica un file Excel e lo importa come DataSource."""
        file = request.FILES.get('file')
        name = request.data.get('name')
        label = request.data.get('label', name)

        if not file or not name:
            return Response(
                {'detail': 'I campi "file" e "name" sono obbligatori.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        suffix = os.path.splitext(file.name)[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            for chunk in file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        try:
            embedding_provider = get_embedding_provider()
            result = import_file(tmp_path, name, label, embedding_provider, owner=request.user)
        except (FileNotFoundError, ValueError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        finally:
            os.unlink(tmp_path)

        return Response(result, status=status.HTTP_200_OK)


class RecordViewSet(viewsets.ModelViewSet):
    serializer_class = RecordSerializer

    def get_queryset(self):
        queryset = (
            Record.objects
            .filter(data_source__owner=self.request.user)
            .select_related('data_source')
            .prefetch_related('attachments', 'history')
        )
        data_source_id = self.request.query_params.get('data_source')
        if data_source_id:
            queryset = queryset.filter(data_source_id=data_source_id)
        return queryset

    def perform_update(self, serializer):
        record = self.get_object()
        old_data = record.data
        updated = serializer.save()

        # Traccia le modifiche campo per campo
        for field, new_value in updated.data.items():
            old_value = old_data.get(field)
            if old_value != new_value:
                RecordHistory.objects.create(
                    record=updated,
                    changed_by=self.request.user,
                    field_changed=field,
                    old_value=str(old_value),
                    new_value=str(new_value),
                )

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        record = self.get_object()
        history = RecordHistory.objects.filter(record=record).order_by('-changed_at')
        serializer = RecordHistorySerializer(history, many=True)
        return Response(serializer.data)


class AttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = AttachmentSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_queryset(self):
        queryset = (
            Attachment.objects
            .filter(record__data_source__owner=self.request.user)
            .select_related('record', 'uploaded_by')
        )
        record_id = self.request.query_params.get('record')
        if record_id:
            queryset = queryset.filter(record_id=record_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

import os
import re
import tempfile

from django.db import connection, transaction
from django.http import HttpResponse
from rest_framework import viewsets, status, parsers
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from crm.models import Attachment, DataSource, MapPin, Note, Record, RecordComment, RecordHistory, StageTemplate, UserProfile
from crm.serializers import (
    AttachmentSerializer,
    DataSourceSerializer,
    MapPinSerializer,
    NoteSerializer,
    RecordCommentSerializer,
    RecordHistorySerializer,
    RecordSerializer,
    StageTemplateSerializer,
    UserProfileSerializer,
)
from crm.services.excel_export import export_datasource, export_group
from crm.services.pdf_export import export_datasource_pdf, export_group_pdf
from crm.services.excel_import import import_all_sheets, get_sheet_names, preview_sheets
from crm.services.embedding import get_embedding_provider


_SAFE_COL_RE = re.compile(r'^[\w ]+\Z')


def _safe_filename(name: str) -> str:
    """Rimuove caratteri non sicuri per Content-Disposition filename."""
    return re.sub(r'[^\w \-.]', '', name).strip() or 'export'


def _save_temp_file(file) -> str:
    """Salva un file in upload in un file temporaneo e restituisce il path."""
    suffix = os.path.splitext(file.name)[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        for chunk in file.chunks():
            tmp.write(chunk)
        return tmp.name


class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        UserProfile.objects.get_or_create(user=self.request.user)
        return UserProfile.objects.filter(user=self.request.user).select_related('user')

    @action(detail=True, methods=['patch'], url_path='api-key')
    def update_api_key(self, request, pk=None):
        """Aggiorna solo la personal_api_key del profilo autenticato.
        Endpoint dedicato per non esporre altri campi del profilo a modifiche accidentali.
        La chiave viene salvata così com'è; un valore vuoto la cancella.
        """
        profile = self.get_object()  # già filtrato per request.user → impossibile modificare profili altrui
        raw_key = request.data.get('personal_api_key', '').strip()
        profile.personal_api_key = raw_key if raw_key else None
        profile.save(update_fields=['personal_api_key'])
        return Response({'detail': 'API key aggiornata.'})

    @action(detail=True, methods=['patch'], url_path='ai-context')
    def update_ai_context(self, request, pk=None):
        profile = self.get_object()
        profile.ai_context = request.data.get('ai_context', '')
        profile.save(update_fields=['ai_context'])
        return Response({'detail': 'Contesto AI aggiornato.'})


class DataSourceViewSet(viewsets.ModelViewSet):
    serializer_class = DataSourceSerializer

    def get_queryset(self):
        return DataSource.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # ── Gestione colonne ────────────────────────────────────────────────────

    @action(detail=True, methods=['post'], url_path='columns')
    def manage_column(self, request, pk=None):
        """Aggiunge, rinomina o elimina una colonna e aggiorna tutti i record via JSONB."""
        ds = self.get_object()
        operation = request.data.get('operation')

        if operation == 'add':
            name = request.data.get('name', '').strip()
            if not name:
                return Response({'detail': 'Il nome è obbligatorio.'}, status=status.HTTP_400_BAD_REQUEST)
            if name in ds.columns:
                return Response({'detail': 'Colonna già esistente.'}, status=status.HTTP_400_BAD_REQUEST)
            with transaction.atomic():
                ds.columns = ds.columns + [name]
                ds.save()
                with connection.cursor() as cur:
                    cur.execute(
                        "UPDATE crm_record SET data = data || jsonb_build_object(%s, NULL) WHERE data_source_id = %s",
                        [name, ds.id],
                    )

        elif operation == 'rename':
            old, new = request.data.get('old_name', '').strip(), request.data.get('new_name', '').strip()
            if not old or not new:
                return Response({'detail': 'old_name e new_name sono obbligatori.'}, status=status.HTTP_400_BAD_REQUEST)
            if old not in ds.columns:
                return Response({'detail': 'Colonna non trovata.'}, status=status.HTTP_404_NOT_FOUND)
            if new in ds.columns:
                return Response({'detail': 'Nome già in uso.'}, status=status.HTTP_400_BAD_REQUEST)
            with transaction.atomic():
                ds.columns = [new if c == old else c for c in ds.columns]
                ds.save()
                with connection.cursor() as cur:
                    cur.execute(
                        "UPDATE crm_record SET data = (data - %s) || jsonb_build_object(%s, data->%s) WHERE data_source_id = %s",
                        [old, new, old, ds.id],
                    )

        elif operation == 'delete':
            name = request.data.get('name', '').strip()
            if not name or name not in ds.columns:
                return Response({'detail': 'Colonna non trovata.'}, status=status.HTTP_404_NOT_FOUND)
            with transaction.atomic():
                ds.columns = [c for c in ds.columns if c != name]
                ds.save()
                with connection.cursor() as cur:
                    cur.execute(
                        "UPDATE crm_record SET data = data - %s WHERE data_source_id = %s",
                        [name, ds.id],
                    )
        elif operation == 'reorder':
            new_order = request.data.get('columns', [])
            if not isinstance(new_order, list) or set(new_order) != set(ds.columns):
                return Response(
                    {'detail': 'columns deve contenere esattamente le stesse colonne esistenti.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ds.columns = new_order
            ds.save()

        else:
            return Response({'detail': 'operation deve essere add, rename, delete o reorder.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(DataSourceSerializer(ds).data)

    @action(detail=True, methods=['patch'], url_path='stages')
    def update_stages(self, request, pk=None):
        """Aggiorna la lista degli stage configurati per questo datasource."""
        ds = self.get_object()
        stages = request.data.get('stages')
        if not isinstance(stages, list) or not all(isinstance(s, str) and s.strip() for s in stages):
            return Response({'detail': 'stages deve essere una lista di stringhe non vuote.'}, status=status.HTTP_400_BAD_REQUEST)
        ds.stages = [s.strip() for s in stages]
        ds.save()
        return Response(DataSourceSerializer(ds).data)

    # ── Operazioni di gruppo ────────────────────────────────────────────────

    @action(detail=False, methods=['patch'], url_path='rename_group')
    def rename_group(self, request):
        """Rinomina tutti i DataSource con lo stesso source_file."""
        source_file = request.data.get('source_file')
        new_name = request.data.get('new_name', '').strip()
        if not source_file or not new_name:
            return Response({'detail': 'source_file e new_name sono obbligatori.'}, status=status.HTTP_400_BAD_REQUEST)
        updated = DataSource.objects.filter(owner=request.user, source_file=source_file).update(source_file=new_name)
        return Response({'updated': updated, 'new_name': new_name})

    @action(detail=False, methods=['delete'], url_path='delete_group')
    def delete_group(self, request):
        """Elimina tutti i DataSource (e i record) con lo stesso source_file."""
        source_file = request.query_params.get('source_file')
        if not source_file:
            return Response({'detail': 'source_file è obbligatorio.'}, status=status.HTTP_400_BAD_REQUEST)
        deleted, _ = DataSource.objects.filter(owner=request.user, source_file=source_file).delete()
        return Response({'deleted': deleted})

    # ── Import / Export ─────────────────────────────────────────────────────

    @action(detail=False, methods=['post'], parser_classes=[parsers.MultiPartParser])
    def preview(self, request):
        """Restituisce un'anteprima dei fogli senza importare."""
        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'Il campo "file" è obbligatorio.'}, status=status.HTTP_400_BAD_REQUEST)
        tmp_path = _save_temp_file(file)
        try:
            sheets = preview_sheets(tmp_path)
        except (FileNotFoundError, ValueError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        finally:
            os.unlink(tmp_path)
        return Response({'sheets': sheets})

    @action(detail=False, methods=['post'], parser_classes=[parsers.MultiPartParser])
    def upload(self, request):
        """Importa tutti i fogli di un file Excel come DataSource separati."""
        file = request.FILES.get('file')
        name = request.data.get('name')
        if not file or not name:
            return Response({'detail': 'I campi "file" e "name" sono obbligatori.'}, status=status.HTTP_400_BAD_REQUEST)
        tmp_path = _save_temp_file(file)
        try:
            from django.core.exceptions import ValidationError as DjangoValidationError
            embedding_provider = get_embedding_provider()
            result = import_all_sheets(tmp_path, source_file=name, embedding_provider=embedding_provider, owner=request.user)
        except (FileNotFoundError, ValueError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except DjangoValidationError as e:
            return Response({'detail': e.message_dict if hasattr(e, 'message_dict') else str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': f'Errore imprevisto: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            os.unlink(tmp_path)
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """Esporta il DataSource come file .xlsx o .pdf (query param: format=pdf)."""
        ds = self.get_object()
        fmt = request.query_params.get('fmt', 'xlsx')
        safe_name = _safe_filename(ds.name)
        if fmt == 'pdf':
            data = export_datasource_pdf(ds)
            response = HttpResponse(data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{safe_name}.pdf"'
        else:
            data = export_datasource(ds)
            response = HttpResponse(
                data,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            response['Content-Disposition'] = f'attachment; filename="{safe_name}.xlsx"'
        return response

    @action(detail=False, methods=['get'], url_path='export_group')
    def export_group(self, request):
        """Esporta tutti i DataSource di un source_file in un unico file (xlsx o pdf)."""
        source_file = request.query_params.get('source_file')
        if not source_file:
            return Response({'detail': 'source_file è obbligatorio.'}, status=status.HTTP_400_BAD_REQUEST)
        data_sources = list(DataSource.objects.filter(owner=request.user, source_file=source_file))
        if not data_sources:
            return Response({'detail': 'Nessun datasource trovato.'}, status=status.HTTP_404_NOT_FOUND)
        safe_name = _safe_filename(source_file)
        fmt = request.query_params.get('fmt', 'xlsx')
        if fmt == 'pdf':
            data = export_group_pdf(data_sources)
            response = HttpResponse(data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{safe_name}.pdf"'
        else:
            data = export_group(data_sources)
            response = HttpResponse(
                data,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            response['Content-Disposition'] = f'attachment; filename="{safe_name}.xlsx"'
        return response

    @action(detail=False, methods=['post'], parser_classes=[parsers.MultiPartParser])
    def sheets(self, request):
        """Restituisce i nomi dei fogli senza importare (usato dall'import form)."""
        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'Il campo "file" è obbligatorio.'}, status=status.HTTP_400_BAD_REQUEST)
        tmp_path = _save_temp_file(file)
        try:
            sheets = get_sheet_names(tmp_path)
        except (FileNotFoundError, ValueError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        finally:
            os.unlink(tmp_path)
        return Response({'sheets': sheets})


class RecordPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 200


class RecordViewSet(viewsets.ModelViewSet):
    serializer_class = RecordSerializer
    pagination_class = RecordPagination

    def get_queryset(self):
        import json as _json
        from django.db.models.expressions import RawSQL

        queryset = (
            Record.objects
            .filter(data_source__owner=self.request.user)
            .select_related('data_source')
            .prefetch_related('attachments', 'history')
        )

        data_source_id = self.request.query_params.get('data_source')
        if data_source_id:
            queryset = queryset.filter(data_source_id=data_source_id)

        # Favorites filter
        if self.request.query_params.get('is_favorite') == 'true':
            queryset = queryset.filter(is_favorite=True)

        # Stage filter
        stage = self.request.query_params.get('stage')
        if stage is not None:
            queryset = queryset.filter(stage=stage)

        # Full-text search across all JSONB fields
        search = self.request.query_params.get('search', '').strip()
        if search:
            from django.db.models import TextField
            from django.db.models.functions import Cast
            queryset = queryset.annotate(
                _data_text=Cast('data', output_field=TextField())
            ).filter(_data_text__icontains=search)

        # Per-column filters: col_filters={"col": "val"}
        col_filters_raw = self.request.query_params.get('col_filters', '')
        if col_filters_raw:
            try:
                col_filters = _json.loads(col_filters_raw)
                for col, val in col_filters.items():
                    if val and _SAFE_COL_RE.match(col):
                        queryset = queryset.annotate(
                            **{f'_cf_{col}': RawSQL("data->>%s", [col])}
                        ).filter(**{f'_cf_{col}__icontains': val})
            except (ValueError, KeyError):
                pass

        # Ordering
        ordering = self.request.query_params.get('ordering', '')
        if ordering == 'position':
            queryset = queryset.order_by('position', 'id')
        elif ordering == '-position':
            queryset = queryset.order_by('-position', 'id')
        elif ordering:
            desc = ordering.startswith('-')
            col = ordering.lstrip('-')
            if _SAFE_COL_RE.match(col):
                order_expr = RawSQL("data->>%s", [col])
                queryset = queryset.order_by(order_expr.desc() if desc else order_expr)
        else:
            queryset = queryset.order_by('-is_favorite', 'id')

        return queryset

    def perform_create(self, serializer):
        from crm.services.excel_import import INSERT_DATE_COL
        import datetime as _dt
        data_source = serializer.validated_data.get('data_source')
        if data_source and data_source.owner != self.request.user:
            raise PermissionDenied('Non hai accesso a questo DataSource.')
        data = dict(serializer.validated_data.get('data', {}))
        if data_source and INSERT_DATE_COL in (data_source.columns or []):
            data[INSERT_DATE_COL] = _dt.datetime.now().strftime('%d/%m/%Y')
        serializer.save(data=data)

    def perform_update(self, serializer):
        record = self.get_object()
        old_data = record.data
        with transaction.atomic():
            updated = serializer.save()
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

    # ── Azioni singolo record ───────────────────────────────────────────────

    @action(detail=True, methods=['patch'])
    def move(self, request, pk=None):
        """Sposta il record in un altro DataSource dello stesso utente."""
        record = self.get_object()
        target_id = request.data.get('data_source_id')
        if not target_id:
            return Response({'detail': 'data_source_id è obbligatorio.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            target = DataSource.objects.get(id=target_id, owner=request.user)
        except DataSource.DoesNotExist:
            return Response({'detail': 'Foglio non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        record.data_source = target
        record.save()
        return Response(RecordSerializer(record).data)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        record = self.get_object()
        history = RecordHistory.objects.filter(record=record).order_by('-changed_at')
        return Response(RecordHistorySerializer(history, many=True).data)

    # ── Azioni bulk ─────────────────────────────────────────────────────────

    @action(detail=False, methods=['post'], url_path='bulk_delete')
    def bulk_delete(self, request):
        """Elimina più record in una sola operazione."""
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'detail': 'ids è obbligatorio.'}, status=status.HTTP_400_BAD_REQUEST)
        deleted, _ = Record.objects.filter(id__in=ids, data_source__owner=request.user).delete()
        return Response({'deleted': deleted})

    @action(detail=False, methods=['post'], url_path='reorder')
    def reorder(self, request):
        """Salva l'ordine dei record nel kanban. ids = lista ordinata di id."""
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'detail': 'ids è obbligatorio.'}, status=status.HTTP_400_BAD_REQUEST)
        records = Record.objects.filter(id__in=ids, data_source__owner=request.user)
        id_map = {r.id: r for r in records}
        to_update = []
        for position, record_id in enumerate(ids):
            if record_id in id_map:
                id_map[record_id].position = position
                to_update.append(id_map[record_id])
        Record.objects.bulk_update(to_update, ['position'])
        return Response({'updated': len(to_update)})

    @action(detail=False, methods=['post'], url_path='bulk_move')
    def bulk_move(self, request):
        """Sposta più record in un altro DataSource."""
        ids = request.data.get('ids', [])
        target_id = request.data.get('data_source_id')
        if not ids or not target_id:
            return Response({'detail': 'ids e data_source_id sono obbligatori.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            target = DataSource.objects.get(id=target_id, owner=request.user)
        except DataSource.DoesNotExist:
            return Response({'detail': 'Foglio non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        moved = Record.objects.filter(id__in=ids, data_source__owner=request.user).update(data_source=target)
        return Response({'moved': moved})


class RecordCommentViewSet(viewsets.ModelViewSet):
    serializer_class = RecordCommentSerializer

    def get_queryset(self):
        queryset = (
            RecordComment.objects
            .filter(record__data_source__owner=self.request.user)
            .select_related('user')
        )
        record_id = self.request.query_params.get('record')
        if record_id:
            queryset = queryset.filter(record_id=record_id)
        return queryset.order_by('created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


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
        from crm.services.image_compress import compress_image, is_image
        from django.core.files.uploadedfile import InMemoryUploadedFile

        file = self.request.FILES.get('file')
        if file and is_image(file.content_type):
            compressed = compress_image(file)
            new_file = InMemoryUploadedFile(
                file=compressed,
                field_name='file',
                name=file.name.rsplit('.', 1)[0] + '.jpg',
                content_type='image/jpeg',
                size=compressed.getbuffer().nbytes,
                charset=None,
            )
            serializer.save(uploaded_by=self.request.user, file=new_file)
        else:
            serializer.save(uploaded_by=self.request.user)


class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer

    def get_queryset(self):
        return Note.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class StageTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = StageTemplateSerializer

    def get_queryset(self):
        return StageTemplate.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class MapPinViewSet(viewsets.ModelViewSet):
    serializer_class = MapPinSerializer
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        return (
            MapPin.objects
            .filter(record__data_source__owner=self.request.user)
            .select_related('record__data_source')
        )

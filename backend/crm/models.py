from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from pgvector.django import VectorField


class UserProfile(models.Model):
  '''Profilo esteso per ogni collaboratore'''
  user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  personal_api_key = models.CharField(max_length=500, blank=True, null=True)
  ai_context = models.TextField(blank=True, default='')

  def __str__(self):
    return self.user.username
  
class DataSource(models.Model):
  '''Rappresenta un foglio di un file Excel: Clienti, partner, etc...'''
  owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='datasources')
  name = models.CharField(max_length=255)
  label = models.CharField(max_length=255)
  columns = models.JSONField()
  source_file = models.CharField(max_length=255, blank=True, null=True, db_index=True)
  stages = models.JSONField(default=list, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)

  def save(self, *args, **kwargs):
    self.full_clean()
    super().save(*args, **kwargs)

  def clean(self):
    if not isinstance(self.columns, list) or not all(isinstance(c, str) for c in self.columns):
      raise ValidationError({'columns': 'Deve essere una lista di stringhe.'})
    if not isinstance(self.stages, list) or not all(isinstance(s, str) for s in self.stages):
      raise ValidationError({'stages': 'Deve essere una lista di stringhe.'})

  def __str__(self):
    return self.name

class Record(models.Model):
  '''Rappresenta una riga di un DataSource'''
  data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='records')
  data = models.JSONField()
  embedding = VectorField(dimensions=1536, null=True, blank=True)
  is_active = models.BooleanField(default=True)
  is_favorite = models.BooleanField(default=False, db_index=True)
  stage = models.CharField(max_length=100, blank=True, default='', db_index=True)
  position = models.IntegerField(default=0, db_index=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f"Record {self.id} from {self.data_source.name}"
  
class RecordHistory(models.Model):
  '''Rappresenta la cronologia di modifiche di un Record'''
  record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='history')
  changed_at = models.DateTimeField(auto_now_add=True)
  changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='record_changes')
  field_changed = models.CharField(max_length=255)
  old_value = models.TextField(null=True, blank=True)
  new_value = models.TextField(null=True, blank=True)

  def __str__(self):
    return f"History for Record {self.record.id} at {self.changed_at}"
  
class RecordComment(models.Model):
  '''Commento interno su un Record'''
  record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='comments')
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='record_comments')
  text = models.CharField(max_length=2000)
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f"Comment by {self.user} on Record {self.record_id}"


class Attachment(models.Model):
  '''Rappresenta un file allegato a un Record'''

  class FileType(models.TextChoices):
    PHOTO = 'photo', 'Foto'
    PDF = 'pdf', 'PDF'
    DOCUMENT = 'document', 'Documento'
    OTHER = 'other', 'Altro'

  record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='attachments')
  file = models.FileField(upload_to='attachments/%Y/%m/%d/')
  file_type = models.CharField(max_length=20, choices=FileType.choices, default=FileType.OTHER)
  label = models.CharField(max_length=255, blank=True, null=True)
  uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='attachments')
  uploaded_at = models.DateTimeField(auto_now_add=True)

  # Per comodità, estraiamo il nome del file senza il percorso completo
  @property
  def filename(self):
    return self.file.name.split('/')[-1]
  
  @property
  def file_url(self):
    return self.file.url

  def __str__(self):
    return f"{self.get_file_type_display()} – Record {self.record.id}"


class StageTemplate(models.Model):
  '''Modello di stage riutilizzabile'''
  owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stage_templates')
  name = models.CharField(max_length=255)
  stages = models.JSONField()

  class Meta:
    ordering = ['name']
    unique_together = [('owner', 'name')]

  def clean(self):
    if not isinstance(self.stages, list) or not all(isinstance(s, str) for s in self.stages):
      raise ValidationError({'stages': 'Deve essere una lista di stringhe.'})

  def __str__(self):
    return self.name


class Note(models.Model):
  '''Nota personale dell\'utente (taccuino)'''
  owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notes')
  title = models.CharField(max_length=255, default='Senza titolo')
  content = models.TextField(blank=True, default='')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    ordering = ['-updated_at']

  def __str__(self):
    return self.title


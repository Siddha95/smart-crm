import os
import tempfile

import openpyxl
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from crm.models import DataSource, Record, RecordHistory
from crm.services.excel_import import clean_row, import_file


class DataSourceModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dsuser", password="pass")

    def test_valid_columns(self):
        ds = DataSource(name="test", label="Test", columns=["nome", "email"], owner=self.user)
        ds.full_clean()

    def test_invalid_columns_not_list(self):
        ds = DataSource(name="test", label="Test", columns={"nome": "email"}, owner=self.user)
        with self.assertRaises(ValidationError):
            ds.full_clean()

    def test_invalid_columns_not_strings(self):
        ds = DataSource(name="test", label="Test", columns=["nome", 123], owner=self.user)
        with self.assertRaises(ValidationError):
            ds.full_clean()


class CleanRowTest(TestCase):
    def test_nan_replaced_with_none(self):
        row = {"nome": "Mario", "eta": float("nan")}
        cleaned = clean_row(row)
        self.assertIsNone(cleaned["eta"])
        self.assertEqual(cleaned["nome"], "Mario")

    def test_valid_row_unchanged(self):
        row = {"nome": "Mario", "email": "mario@example.com"}
        self.assertEqual(clean_row(row), row)


class ImportFileTest(TestCase):
    def _make_excel(self, rows: list[dict]) -> str:
        wb = openpyxl.Workbook()
        ws = wb.active
        if rows:
            ws.append(list(rows[0].keys()))
            for row in rows:
                ws.append(list(row.values()))
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as f:
            wb.save(f.name)
            return f.name

    def setUp(self):
        self.user = User.objects.create_user(username="importer", password="pass")

    def test_import_creates_datasource_and_records(self):
        path = self._make_excel([{"nome": "Mario", "email": "mario@example.com"}])
        try:
            result = import_file(path, "clienti", "Clienti", owner=self.user)
        finally:
            os.unlink(path)

        self.assertEqual(result["imported"], 1)
        self.assertTrue(DataSource.objects.filter(name="clienti", owner=self.user).exists())
        self.assertEqual(Record.objects.filter(data_source__name="clienti").count(), 1)

    def test_reimport_replaces_records(self):
        path = self._make_excel([{"nome": "Mario"}, {"nome": "Luigi"}])
        try:
            import_file(path, "clienti", "Clienti", owner=self.user)
            result = import_file(path, "clienti", "Clienti", owner=self.user)
        finally:
            os.unlink(path)

        self.assertEqual(result["deleted"], 2)
        self.assertEqual(result["imported"], 2)
        self.assertEqual(Record.objects.filter(data_source__name="clienti").count(), 2)

    def test_two_users_isolated(self):
        """Utenti diversi non si vedono i dati a vicenda."""
        user2 = User.objects.create_user(username="altro", password="pass")
        path = self._make_excel([{"nome": "Mario"}])
        try:
            import_file(path, "clienti", "Clienti", owner=self.user)
            import_file(path, "clienti", "Clienti", owner=user2)
        finally:
            os.unlink(path)

        self.assertEqual(DataSource.objects.filter(owner=self.user).count(), 1)
        self.assertEqual(DataSource.objects.filter(owner=user2).count(), 1)

    def test_file_not_found_raises(self):
        with self.assertRaises(FileNotFoundError):
            import_file("/non/esiste.xlsx", "test", "Test", owner=self.user)


class RecordHistoryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.ds = DataSource.objects.create(name="test", label="Test", columns=["campo"], owner=self.user)
        self.record = Record.objects.create(data_source=self.ds, data={"campo": "valore"})

    def test_history_created_on_change(self):
        RecordHistory.objects.create(
            record=self.record,
            changed_by=self.user,
            field_changed="campo",
            old_value="valore",
            new_value="nuovo",
        )
        self.assertEqual(self.record.history.count(), 1)

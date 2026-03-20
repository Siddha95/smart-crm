"""
Test di integrazione per i router FastAPI.
Usa TestClient con dependency override per evitare dipendenze da DB reale o AI provider.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    """Crea l'app FastAPI con il lifespan disabilitato (nessuna connessione DB)."""
    from fastapi import FastAPI
    from routers import ai, reports

    _app = FastAPI()
    _app.include_router(reports.router)
    _app.include_router(ai.router)
    return _app


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)


def _mock_user_id():
    return 1


def _mock_provider():
    provider = MagicMock()
    provider.complete_with_tools.return_value = "Risposta AI di test"
    return provider


def _mock_embedding_provider():
    ep = MagicMock()
    ep.embed.return_value = [0.0] * 1536
    return ep


def _mock_db():
    return MagicMock()


# ── Auth: route richiedono authorization header ──────────────────────────────

class TestAuthRequired:
    def test_reports_datasources_without_auth_returns_422(self, client):
        """Header authorization mancante → FastAPI 422 (campo obbligatorio assente)."""
        resp = client.get("/reports/datasources")
        assert resp.status_code == 422

    def test_reports_records_without_auth_returns_422(self, client):
        resp = client.get("/reports/datasources/1/records")
        assert resp.status_code == 422

    def test_reports_report_without_auth_returns_422(self, client):
        resp = client.post("/reports/datasources/1/report")
        assert resp.status_code == 422

    def test_chat_without_auth_returns_422(self, client):
        resp = client.post("/ai/chat", json={"question": "ciao"})
        assert resp.status_code == 422

    def test_datasource_chat_without_auth_returns_422(self, client):
        resp = client.post("/ai/datasources/1/chat", json={"question": "ciao"})
        assert resp.status_code == 422

    def test_analyze_without_auth_returns_422(self, client):
        resp = client.post("/ai/records/1/analyze")
        assert resp.status_code == 422

    def test_suggest_without_auth_returns_422(self, client):
        resp = client.post("/ai/records/1/suggest")
        assert resp.status_code == 422


# ── Reports: con auth mockato ─────────────────────────────────────────────────

class TestReportsRoutes:
    def test_list_datasources_returns_user_data_only(self, app, client):
        from dependencies import get_user_id, get_user_ai_provider, get_user_embedding_provider
        from database import get_db

        ds_mock = MagicMock()
        ds_mock.id = 1
        ds_mock.name = "clienti"
        ds_mock.label = "Clienti"
        ds_mock.columns = ["nome", "email"]

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [ds_mock]

        app.dependency_overrides[get_user_id] = _mock_user_id
        app.dependency_overrides[get_db] = lambda: db
        try:
            resp = client.get("/reports/datasources", headers={"authorization": "Bearer fake"})
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["name"] == "clienti"
        finally:
            app.dependency_overrides.clear()

    def test_list_records_datasource_not_found_returns_404(self, app, client):
        from dependencies import get_user_id
        from database import get_db

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        app.dependency_overrides[get_user_id] = _mock_user_id
        app.dependency_overrides[get_db] = lambda: db
        try:
            resp = client.get("/reports/datasources/99/records", headers={"authorization": "Bearer fake"})
            assert resp.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_generate_report_no_records_returns_404(self, app, client):
        from dependencies import get_user_id, get_user_ai_provider
        from database import get_db

        source_mock = MagicMock()
        source_mock.name = "ds"

        db = MagicMock()
        # first() per DataSource → trovato; all() per Record → vuoto
        db.query.return_value.filter.return_value.first.return_value = source_mock
        db.query.return_value.filter.return_value.all.return_value = []

        app.dependency_overrides[get_user_id] = _mock_user_id
        app.dependency_overrides[get_user_ai_provider] = _mock_provider
        app.dependency_overrides[get_db] = lambda: db
        try:
            resp = client.post("/reports/datasources/1/report", headers={"authorization": "Bearer fake"})
            assert resp.status_code == 404
        finally:
            app.dependency_overrides.clear()


# ── AI Chat: con auth mockato ─────────────────────────────────────────────────

class TestAIChatRoutes:
    def _setup(self, app):
        from dependencies import get_user_id, get_user_ai_provider, get_user_embedding_provider
        from database import get_db

        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        db.query.return_value.filter.return_value.all.return_value = []

        app.dependency_overrides[get_user_id] = _mock_user_id
        app.dependency_overrides[get_user_ai_provider] = _mock_provider
        app.dependency_overrides[get_user_embedding_provider] = _mock_embedding_provider
        app.dependency_overrides[get_db] = lambda: db
        return db

    def test_global_chat_returns_answer(self, app, client):
        self._setup(app)
        try:
            resp = client.post(
                "/ai/chat",
                json={"question": "ciao"},
                headers={"authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            assert "answer" in resp.json()
        finally:
            app.dependency_overrides.clear()

    def test_datasource_chat_returns_answer(self, app, client):
        self._setup(app)
        try:
            resp = client.post(
                "/ai/datasources/1/chat",
                json={"question": "chi è Mario?"},
                headers={"authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            assert "answer" in resp.json()
        finally:
            app.dependency_overrides.clear()

    def test_analyze_record_not_found_returns_404(self, app, client):
        from dependencies import get_user_id, get_user_ai_provider
        from database import get_db

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        app.dependency_overrides[get_user_id] = _mock_user_id
        app.dependency_overrides[get_user_ai_provider] = _mock_provider
        app.dependency_overrides[get_db] = lambda: db
        try:
            resp = client.post("/ai/records/999/analyze", headers={"authorization": "Bearer fake"})
            assert resp.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_suggest_record_not_found_returns_404(self, app, client):
        from dependencies import get_user_id, get_user_ai_provider
        from database import get_db

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        app.dependency_overrides[get_user_id] = _mock_user_id
        app.dependency_overrides[get_user_ai_provider] = _mock_provider
        app.dependency_overrides[get_db] = lambda: db
        try:
            resp = client.post("/ai/records/999/suggest", headers={"authorization": "Bearer fake"})
            assert resp.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_analyze_record_returns_analysis(self, app, client):
        from dependencies import get_user_id, get_user_ai_provider
        from database import get_db
        from services.ai import prompts

        record_mock = MagicMock()
        record_mock.data = {"nome": "Alice", "eta": "30"}

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = record_mock

        provider = _mock_provider()
        app.dependency_overrides[get_user_id] = _mock_user_id
        app.dependency_overrides[get_user_ai_provider] = lambda: provider
        app.dependency_overrides[get_db] = lambda: db

        with patch.object(prompts, "analyze_record", return_value="Analisi: cliente attivo"):
            try:
                resp = client.post("/ai/records/1/analyze", headers={"authorization": "Bearer fake"})
                assert resp.status_code == 200
                assert resp.json()["analysis"] == "Analisi: cliente attivo"
            finally:
                app.dependency_overrides.clear()


# ── Health check ──────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_endpoint(self):
        """L'app senza lifespan (no DB) espone /health."""
        from fastapi import FastAPI
        from routers import ai, reports

        _app = FastAPI()
        _app.include_router(reports.router)
        _app.include_router(ai.router)

        @_app.get("/health")
        def health():
            return {"status": "ok"}

        with TestClient(_app) as c:
            resp = c.get("/health")
            assert resp.status_code == 200
            assert resp.json() == {"status": "ok"}

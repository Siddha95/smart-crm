"""
Unit test per dependencies.py — JWT decode, autorizzazione, edge case.
Non richiede un database reale: la sessione SQLAlchemy viene mockata.
"""
import jwt
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException


def _token(secret: str, user_id: int) -> str:
    return jwt.encode({"user_id": user_id}, secret, algorithm="HS256")


def _make_db(api_key: str | None = "sk-test-key") -> MagicMock:
    """Restituisce un mock di Session con un UserProfile configurato."""
    db = MagicMock()
    if api_key is not None:
        profile = MagicMock()
        profile.personal_api_key = api_key
        db.query.return_value.filter.return_value.first.return_value = profile
    else:
        db.query.return_value.filter.return_value.first.return_value = None
    return db


@pytest.fixture(autouse=True)
def patch_secret(monkeypatch):
    """Imposta un secret fisso per tutti i test."""
    import dependencies
    monkeypatch.setattr(dependencies.settings, "django_secret_key", "testsecret")
    return "testsecret"


SECRET = "testsecret"


class TestResolveUser:
    def test_valid_token_returns_user_id_and_key(self):
        from dependencies import _resolve_user

        token = _token(SECRET, 42)
        user_id, api_key = _resolve_user(f"Bearer {token}", _make_db("sk-ant-test"))
        assert user_id == 42
        assert api_key == "sk-ant-test"

    def test_missing_bearer_prefix_raises_401(self):
        from dependencies import _resolve_user

        with pytest.raises(HTTPException) as exc:
            _resolve_user("notbearer token", _make_db())
        assert exc.value.status_code == 401

    def test_invalid_token_raises_401(self):
        from dependencies import _resolve_user

        with pytest.raises(HTTPException) as exc:
            _resolve_user("Bearer invalid.token.here", _make_db())
        assert exc.value.status_code == 401

    def test_token_signed_with_wrong_secret_raises_401(self):
        from dependencies import _resolve_user

        token = _token("wrong-secret", 1)
        with pytest.raises(HTTPException) as exc:
            _resolve_user(f"Bearer {token}", _make_db())
        assert exc.value.status_code == 401

    def test_no_profile_raises_403(self):
        from dependencies import _resolve_user

        token = _token(SECRET, 99)
        with pytest.raises(HTTPException) as exc:
            _resolve_user(f"Bearer {token}", _make_db(api_key=None))
        assert exc.value.status_code == 403

    def test_empty_api_key_raises_403(self):
        from dependencies import _resolve_user

        token = _token(SECRET, 1)
        with pytest.raises(HTTPException) as exc:
            _resolve_user(f"Bearer {token}", _make_db(api_key=""))
        assert exc.value.status_code == 403

    def test_token_missing_user_id_raises_401(self):
        from dependencies import _resolve_user

        # Token valido ma senza campo user_id
        token = jwt.encode({"sub": "anonymous"}, SECRET, algorithm="HS256")
        with pytest.raises(HTTPException) as exc:
            _resolve_user(f"Bearer {token}", _make_db())
        assert exc.value.status_code == 401


class TestGetUserAiProvider:
    def test_claude_key_returns_claude_provider(self):
        from dependencies import get_user_ai_provider
        from services.ai.claude import ClaudeProvider

        token = _token(SECRET, 1)
        db = _make_db(api_key="sk-ant-my-claude-key")
        with patch("dependencies._resolve_user", return_value=(1, "sk-ant-my-claude-key")):
            provider = get_user_ai_provider(authorization=f"Bearer {token}", db=db)
        assert isinstance(provider, ClaudeProvider)

    def test_openai_key_returns_openai_provider(self):
        from dependencies import get_user_ai_provider
        from services.ai.openai import OpenAIProvider

        token = _token(SECRET, 1)
        db = _make_db(api_key="sk-openai-key")
        with patch("dependencies._resolve_user", return_value=(1, "sk-openai-key")):
            provider = get_user_ai_provider(authorization=f"Bearer {token}", db=db)
        assert isinstance(provider, OpenAIProvider)


class TestGetUserEmbeddingProvider:
    def test_openai_key_returns_provider(self):
        from dependencies import get_user_embedding_provider

        with patch("dependencies._resolve_user", return_value=(1, "sk-openai-key")):
            provider = get_user_embedding_provider(authorization="Bearer t", db=MagicMock())
        assert provider is not None

    def test_claude_key_without_global_fallback_raises_403(self):
        from dependencies import get_user_embedding_provider
        import dependencies

        with patch("dependencies._resolve_user", return_value=(1, "sk-ant-key")):
            with patch.object(dependencies.settings, "openai_api_key", ""):
                with pytest.raises(HTTPException) as exc:
                    get_user_embedding_provider(authorization="Bearer t", db=MagicMock())
        assert exc.value.status_code == 403

    def test_claude_key_with_global_fallback_returns_provider(self):
        from dependencies import get_user_embedding_provider
        import dependencies

        with patch("dependencies._resolve_user", return_value=(1, "sk-ant-key")):
            with patch.object(dependencies.settings, "openai_api_key", "sk-global-openai"):
                provider = get_user_embedding_provider(authorization="Bearer t", db=MagicMock())
        assert provider is not None

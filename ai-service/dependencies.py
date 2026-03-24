from functools import lru_cache

import jwt
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ai_config import settings
from database import get_db
from models import UserProfile
from services.ai.base import AIProvider
from services.ai.factory import get_provider
from services.embeddings.base import EmbeddingProvider
from services.embeddings.factory import get_embedding_provider


@lru_cache
def get_ai_provider() -> AIProvider:
    return get_provider(
        claude_api_key=settings.claude_api_key or None,
        openai_api_key=settings.openai_api_key or None,
    )


@lru_cache
def get_embedding_provider_dep() -> EmbeddingProvider:
    return get_embedding_provider(openai_api_key=settings.openai_api_key or None)


def _resolve_user(authorization: str, db: Session) -> tuple[int, str]:
    """Decodifica il JWT e restituisce (user_id, personal_api_key)."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token non valido.")
    token = authorization.split(" ", 1)[1]

    try:
        payload = jwt.decode(token, settings.django_secret_key, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token scaduto o non valido.")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token non valido.")

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    api_key = profile.personal_api_key if profile else None

    if not api_key:
        raise HTTPException(
            status_code=403,
            detail="Nessuna API key configurata. Aggiungila nelle impostazioni.",
        )
    return user_id, api_key


def get_user_id(
    authorization: str = Header(...),
    db: Session = Depends(get_db),
) -> int:
    user_id, _ = _resolve_user(authorization, db)
    return user_id


def get_user_ai_provider(
    authorization: str = Header(...),
    db: Session = Depends(get_db),
) -> AIProvider:
    _, api_key = _resolve_user(authorization, db)
    return get_provider(
        claude_api_key=api_key if api_key.startswith("sk-ant") else None,
        openai_api_key=api_key if not api_key.startswith("sk-ant") else None,
    )


def get_user_embedding_provider(
    authorization: str = Header(...),
    db: Session = Depends(get_db),
) -> EmbeddingProvider:
    """Usa la chiave OpenAI dell'utente per gli embeddings; fallback alla chiave globale."""
    _, api_key = _resolve_user(authorization, db)

    # Gli embeddings richiedono OpenAI — Claude non espone API di embeddings
    openai_key = None
    if not api_key.startswith("sk-ant"):
        openai_key = api_key  # è una chiave OpenAI
    elif settings.openai_api_key:
        openai_key = settings.openai_api_key  # fallback globale

    if not openai_key:
        raise HTTPException(
            status_code=403,
            detail="Gli embeddings richiedono una chiave OpenAI. Aggiungila nelle impostazioni o configura OPENAI_API_KEY sul server.",
        )
    return get_embedding_provider(openai_api_key=openai_key)

from functools import lru_cache

from config import settings
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

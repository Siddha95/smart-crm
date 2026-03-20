from services.embeddings.base import EmbeddingProvider
from services.embeddings.openai import OpenAIEmbeddingProvider


def get_embedding_provider(openai_api_key: str = None) -> EmbeddingProvider:
    """Restituisce il provider di embeddings disponibile.

    Per ora supporta solo OpenAI — Anthropic non espone API di embeddings.
    """
    if openai_api_key:
        return OpenAIEmbeddingProvider(api_key=openai_api_key)
    raise ValueError("Nessuna API key per embeddings configurata. Imposta OPENAI_API_KEY.")

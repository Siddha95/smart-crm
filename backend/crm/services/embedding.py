from django.conf import settings
from openai import OpenAI


def record_to_text(data: dict) -> str:
    """Serializza un record CRM in testo per la generazione dell'embedding."""
    return " ".join(f"{k}: {v}" for k, v in data.items() if v is not None)


class OpenAIEmbeddingProvider:
    # text-embedding-3-small: 1536 dimensioni, economico e preciso per testi CRM
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def embed(self, text: str) -> list[float]:
        response = self._client.embeddings.create(input=text, model=self._model)
        if not response.data:
            raise ValueError("OpenAI ha restituito un embedding vuoto.")
        return response.data[0].embedding

    def embed_record(self, data: dict) -> list[float]:
        return self.embed(record_to_text(data))


def get_embedding_provider() -> OpenAIEmbeddingProvider | None:
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    if not api_key:
        return None
    return OpenAIEmbeddingProvider(api_key=api_key)

from openai import OpenAI

from services.embeddings.base import EmbeddingProvider


class OpenAIEmbeddingProvider(EmbeddingProvider):
    # text-embedding-3-small: 1536 dimensioni, economico e preciso per testi CRM
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def embed(self, text: str) -> list[float]:
        response = self._client.embeddings.create(input=text, model=self._model)
        if not response.data:
            raise ValueError("OpenAI ha restituito un embedding vuoto.")
        return response.data[0].embedding

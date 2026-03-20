from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Interfaccia comune per tutti i provider di embeddings."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Converte un testo in un vettore di embedding."""
        ...


def record_to_text(data: dict) -> str:
    """Serializza un record CRM in testo per la generazione dell'embedding."""
    return " ".join(f"{k}: {v}" for k, v in data.items() if v is not None)

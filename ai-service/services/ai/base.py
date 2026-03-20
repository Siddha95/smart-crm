from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Interfaccia comune per tutti i provider AI."""

    @abstractmethod
    def complete(self, prompt: str) -> str:
        """Invia un prompt al modello e restituisce la risposta."""
        ...

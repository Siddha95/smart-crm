from abc import ABC, abstractmethod
from typing import Callable


class AIProvider(ABC):
    """Interfaccia comune per tutti i provider AI."""

    @abstractmethod
    def complete(self, prompt: str) -> str:
        """Invia un prompt al modello e restituisce la risposta."""
        ...

    @abstractmethod
    def complete_with_tools(
        self,
        messages: list,
        tools: list,
        tool_executor: Callable[[str, dict], str],
        system: str = "",
    ) -> str:
        """Loop agentico con tool use. Restituisce la risposta finale testuale."""
        ...

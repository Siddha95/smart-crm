from services.ai.base import AIProvider
from services.ai.claude import ClaudeProvider
from services.ai.openai import OpenAIProvider


def get_provider(claude_api_key: str = None, openai_api_key: str = None) -> AIProvider:
    """Restituisce il provider AI in base alle API key disponibili.

    Claude ha priorità su OpenAI se entrambe le chiavi sono presenti.
    """
    if claude_api_key:
        return ClaudeProvider(api_key=claude_api_key)
    if openai_api_key:
        return OpenAIProvider(api_key=openai_api_key)
    raise ValueError("Nessuna API key AI configurata. Imposta CLAUDE_API_KEY o OPENAI_API_KEY.")

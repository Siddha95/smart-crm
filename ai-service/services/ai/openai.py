from openai import OpenAI

from services.ai.base import AIProvider


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def complete(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
        )
        if not response.choices:
            raise ValueError("OpenAI ha restituito una risposta vuota.")
        return response.choices[0].message.content

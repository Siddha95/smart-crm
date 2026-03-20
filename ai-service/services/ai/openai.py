import json
from typing import Callable

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

    @staticmethod
    def _convert_tools(tools: list) -> list:
        """Converte dal formato Claude (input_schema) al formato OpenAI (function/parameters)."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            }
            for t in tools
        ]

    def complete_with_tools(
        self,
        messages: list,
        tools: list,
        tool_executor: Callable[[str, dict], str],
        system: str = "",
    ) -> str:
        all_messages = ([{"role": "system", "content": system}] if system else []) + messages
        openai_tools = self._convert_tools(tools)
        while True:
            response = self._client.chat.completions.create(
                model=self._model,
                tools=openai_tools,
                messages=all_messages,
            )
            msg = response.choices[0].message
            if msg.tool_calls:
                all_messages.append(msg)
                for call in msg.tool_calls:
                    result = tool_executor(call.function.name, json.loads(call.function.arguments))
                    all_messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result,
                    })
            else:
                return msg.content or ""

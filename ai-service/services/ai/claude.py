from typing import Callable

import anthropic

from services.ai.base import AIProvider


class ClaudeProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete(self, prompt: str) -> str:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        if not message.content:
            raise ValueError("Claude ha restituito una risposta vuota.")
        return message.content[0].text

    def complete_with_tools(
        self,
        messages: list,
        tools: list,
        tool_executor: Callable[[str, dict], str],
        system: str = "",
    ) -> str:
        kwargs = {"system": system} if system else {}
        while True:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=2048,
                tools=tools,
                messages=messages,
                **kwargs,
            )
            if response.stop_reason == "tool_use":
                tool_results = [
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_executor(block.name, block.input),
                    }
                    for block in response.content
                    if block.type == "tool_use"
                ]
                messages = messages + [
                    {"role": "assistant", "content": response.content},
                    {"role": "user", "content": tool_results},
                ]
            else:
                return next((b.text for b in response.content if hasattr(b, "text")), "")

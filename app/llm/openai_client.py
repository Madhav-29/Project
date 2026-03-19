from __future__ import annotations

import os

from app.llm.base import ChatMessage, LLMClient


class OpenAIChatClient(LLMClient):
    def __init__(self, model: str | None = None) -> None:
        from openai import OpenAI

        self.client = OpenAI()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    def complete(self, messages: list[ChatMessage]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": message.role, "content": message.content} for message in messages],
            temperature=0.1,
        )
        return response.choices[0].message.content or ""

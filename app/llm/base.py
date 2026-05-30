from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChatMessage:
    role: str
    content: str


class LLMClient:
    def complete(self, messages: list[ChatMessage]) -> str:
        raise NotImplementedError

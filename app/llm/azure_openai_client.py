from __future__ import annotations

import os

from app.llm.base import ChatMessage, LLMClient


class AzureOpenAIChatClient(LLMClient):
    def __init__(self) -> None:
        from openai import AzureOpenAI

        self.client = AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        )
        self.deployment = os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"]

    def complete(self, messages: list[ChatMessage]) -> str:
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[{"role": message.role, "content": message.content} for message in messages],
            temperature=0.1,
        )
        return response.choices[0].message.content or ""

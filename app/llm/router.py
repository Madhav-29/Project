from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from app.llm.azure_openai_client import AzureOpenAIChatClient
from app.llm.base import LLMClient
from app.llm.openai_client import OpenAIChatClient

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)


class StubLLMClient(LLMClient):
    def complete(self, messages):
        return (
            "AI Assistant synthesis is unavailable because LLM credentials are not configured. "
            "Structured rules and retrieved synthetic evidence are still available for review."
        )


def get_llm_client() -> LLMClient:
    if os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_API_KEY"):
        return AzureOpenAIChatClient()
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIChatClient()
    return StubLLMClient()


def has_llm_credentials() -> bool:
    return bool(
        (os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_API_KEY"))
        or os.getenv("OPENAI_API_KEY")
    )

"""
OpenAI SDK 직접 사용 LLM 클라이언트.

[Gemini 클라이언트와 같은 인터페이스 — generate(prompt) -> str]
"""
from __future__ import annotations

import os

from openai import OpenAI


class DirectOpenAIClient:
    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        api_key: str | None = None,
    ) -> None:
        self.model_name = model_name
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY 필요")
        self._client = OpenAI(api_key=key)

    def generate(self, prompt: str) -> str:
        # OpenAI는 messages 형식 — 단순화 위해 user 메시지 1개로 wrap
        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

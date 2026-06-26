"""
Gemini SDK 직접 사용 LLM 클라이언트 (새 SDK: google-genai).

[책임]
- 인증 + 모델 선택
- generate(prompt) -> str

이 클래스는 RAG/검색/임베딩을 모른다. 오직 LLM 호출만.

[새 SDK 차이 — google-generativeai → google-genai (2025 통합)]
- import: from google import genai (옛: import google.generativeai as genai)
- 인증: genai.Client(api_key=...) (옛: 전역 genai.configure)
- 호출: client.models.generate_content(model=name, contents=prompt)

새 SDK는 Vertex AI와 Gemini API를 같은 인터페이스로 통합한다.
Client 객체 단위로 인증해서 멀티 클라이언트도 쉬움.
"""
from __future__ import annotations

import os

from google import genai


class DirectGeminiClient:
    def __init__(
        self,
        model_name: str = "gemini-flash-latest",
        api_key: str | None = None,
    ) -> None:
        self.model_name = model_name
        key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GOOGLE_API_KEY (또는 GEMINI_API_KEY) 필요")
        # 새 SDK: Client 객체 만들기 (옛 SDK는 전역 configure)
        self._client = genai.Client(api_key=key)

    def generate(self, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        return response.text

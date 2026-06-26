"""
LLM 클라이언트의 공통 인터페이스 (Protocol).

[메커니즘 설명]
Python의 typing.Protocol을 쓰면 "이 메서드들을 가진 객체면 누구든 OK" 라는
duck typing 계약을 만들 수 있다. 상속 없이 인터페이스 강제.

RAG Chain은 이 Protocol 타입을 받게 해서, GPT/Gemini/Claude 무엇이 들어와도
generate(prompt) 메서드만 있으면 동작.
"""
from typing import Protocol


class LLMClient(Protocol):
    """모든 LLM 클라이언트가 따라야 할 인터페이스."""

    model_name: str

    def generate(self, prompt: str) -> str:
        """프롬프트를 LLM에 전달하고 답변 텍스트 반환."""
        ...

"""
mimeType별 LangChain parser dispatcher.

[메커니즘 설명]
direct_dispatcher와 동일한 Registry 패턴이지만 반환 타입이 다르다:
  - direct_dispatcher.parse_file(bytes, mime) -> str
  - langchain_dispatcher.parse_file_to_documents(bytes, mime, metadata) -> list[Document]

LangChain 버전에서 metadata 매개변수가 추가된 이유:
  Document.metadata는 LangChain의 핵심 자산이다. 인덱싱 시 file_id, file_name,
  mime_type, modified_time 등을 미리 박아두면 검색 시 강력한 필터링이 가능하다
  (예: where={"mime_type": "application/pdf"}). 그래서 입력 시점에 받아둔다.

[Open/Closed 원칙]
새 mimeType 지원 시 PARSER_REGISTRY에 한 줄만 추가하면 된다. dispatcher 본체 수정 X.
"""
from __future__ import annotations

from typing import Callable

from langchain_core.documents import Document

from app.rag_drive_search.services.parsers.langchain_markdown_parser import (
    parse_markdown_to_documents,
)
from app.rag_drive_search.services.parsers.langchain_pdf_parser import (
    parse_pdf_to_documents,
)
from app.rag_drive_search.services.parsers.langchain_google_docs_parser import (
    parse_google_doc_text_to_documents,
)


# 타입 알리어스: parser 함수의 시그니처
# (bytes, metadata 옵션) -> Document list
ParserFunc = Callable[[bytes, dict | None], list[Document]]


# mimeType → parser 함수 매핑.
# Direct 버전과 동일한 키. 값(함수)의 시그니처만 다르다.
PARSER_REGISTRY: dict[str, ParserFunc] = {
    "text/markdown": parse_markdown_to_documents,
    "application/pdf": parse_pdf_to_documents,
    "application/vnd.google-apps.document": parse_google_doc_text_to_documents,
}


def parse_file_to_documents(
    file_bytes: bytes,
    mime_type: str,
    metadata: dict | None = None,
) -> list[Document]:
    """
    mimeType에 맞는 LangChain parser를 골라서 Document list 반환.

    Args:
        file_bytes: 파일 raw bytes
        mime_type: 파일의 mimeType
        metadata: 각 Document에 추가될 메타데이터 (file_id, file_name 등)

    Returns:
        Document 객체의 list (PDF는 페이지 수만큼, 나머지는 1개)

    Raises:
        ValueError: 지원하지 않는 mimeType
    """
    parser = PARSER_REGISTRY.get(mime_type)
    if parser is None:
        raise ValueError(f"Unsupported mime_type: {mime_type}")

    return parser(file_bytes, metadata)


def is_supported(mime_type: str) -> bool:
    """mimeType이 지원되는지 체크 (인덱싱 필터링용)."""
    return mime_type in PARSER_REGISTRY

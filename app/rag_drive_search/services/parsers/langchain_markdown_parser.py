"""
Markdown bytes → LangChain Document 변환.

[메커니즘 설명]
LangChain의 핵심 데이터 단위는 `Document` 객체이다. 이 객체는 두 필드를 가진다:
  - page_content : 텍스트 본문 (str)
  - metadata     : 출처/페이지/파일ID 등 dict

LangChain pipeline (Loader → Splitter → Embeddings → VectorStore → Retriever)
은 모두 이 Document 단위로 데이터를 주고받는다.
즉 우리가 어떤 형식의 원본 파일이든 일단 Document로 변환하면 그 다음 모든 단계는
표준화된 인터페이스로 처리할 수 있다.

[왜 TextLoader 안 쓰고 직접 Document를 만드나?]
LangChain의 TextLoader는 "파일 경로"를 받는다. 우리는 Google Drive에서 받은
bytes를 가지고 있으므로 임시 파일을 만들든지 Document를 직접 만들어야 한다.
Markdown은 단순 텍스트라 임시 파일을 거치는 것보다 Document를 직접 만드는 것이
더 단순하고 빠르다.
PDF처럼 페이지 단위 분리가 필요한 포맷은 LangChain Loader를 그대로 사용한다.
"""
from __future__ import annotations

from langchain_core.documents import Document


def parse_markdown_to_documents(
    file_bytes: bytes,
    metadata: dict | None = None,
) -> list[Document]:
    """
    Args:
        file_bytes: Drive에서 받은 raw bytes (markdown 텍스트)
        metadata: 각 Document에 첨부할 메타데이터 (file_id, file_name 등)

    Returns:
        Document 1개를 담은 list (markdown은 페이지 개념 없으므로 1개)
    """
    # 1) bytes → str
    # Markdown은 이미 plain text이므로 utf-8 디코딩만 하면 끝.
    text = file_bytes.decode("utf-8")

    # 2) Document로 wrapping
    # page_content: 본문, metadata: 검색 시 필터링/추적용
    document = Document(
        page_content=text,
        metadata=metadata or {},
    )

    # 3) 일관성을 위해 list로 반환 (PDF는 페이지별로 여러 개 반환하므로)
    return [document]

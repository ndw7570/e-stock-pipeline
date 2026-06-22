"""
LangChain의 RecursiveCharacterTextSplitter로 Document를 청킹.

[메커니즘 설명]
LangChain의 Text Splitter는 직접 구현(direct_text_chunker.py)보다 더 정교하다.
RecursiveCharacterTextSplitter는 **여러 구분자를 순차적으로** 시도한다:

  1. 먼저 "\\n\\n" (단락 경계)으로 자르려 시도
  2. 너무 큰 청크가 있으면 "\\n" (줄 경계)로 다시 시도
  3. 그것도 너무 크면 " " (단어 경계)
  4. 마지막으로 "" (글자 단위)

이 "recursive" 전략 덕분에 의미 단위를 최대한 보존하면서도
청크 크기 제약을 지킨다. 직접 구현은 단락 + 글자 단위만 처리하지만
LangChain은 줄/단어 단위까지 자동 폴백한다.

[입출력 차이 — direct vs LangChain]
  direct  : str (텍스트) -> list[str] (청크 텍스트)
  langchain: list[Document] -> list[Document]

LangChain은 metadata를 자동 복사한다. 각 청크 Document는 원본의
metadata (file_id, file_name 등)을 그대로 가지며, 추가로 chunk index가 박힌다.
이게 D5(인덱싱)와 D6(검색)에서 강력한 필터링/추적의 기반이 된다.
"""
from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_documents(
    documents: list[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
) -> list[Document]:
    """
    LangChain Document list를 청킹해서 더 작은 Document list로 반환.

    Args:
        documents: D3 langchain_dispatcher가 반환한 Document list
        chunk_size: 한 청크의 최대 글자 수 (목표값)
        chunk_overlap: 인접 청크 간 겹치는 글자 수 (맥락 보존)

    Returns:
        청킹된 Document list. 각 Document는:
          - page_content: 청크 텍스트
          - metadata: 원본 metadata + 추가 필드 (start_index 등 splitter가 자동 추가)
    """
    # RecursiveCharacterTextSplitter:
    # - separators: 시도할 구분자 순서 (단락 → 줄 → 단어 → 글자)
    # - length_function: 청크 길이 계산 함수 (기본 len = 글자 수)
    # - add_start_index: True면 metadata['start_index']에 원본 내 위치 추가 (추적용)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
        length_function=len,
        add_start_index=True,
    )

    # split_documents: Document를 입력받아 청킹된 Document list 반환.
    # 각 청크의 metadata는 원본 metadata를 자동 상속.
    return splitter.split_documents(documents)

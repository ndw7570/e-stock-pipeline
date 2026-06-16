"""
Google Docs export bytes → LangChain Document 변환.

[메커니즘 설명]
GoogleDriveClient.download_file()이 Google Docs를 'text/plain'으로 export하므로
받은 bytes는 이미 plain text이다. markdown과 마찬가지로 단순 wrapping만 하면 된다.

[왜 markdown parser와 코드가 동일한가?]
입력 bytes의 의미가 다르다:
  - markdown : 원본이 markdown 문법 텍스트
  - google docs: GoogleDriveClient가 export한 plain text (포맷팅 X)
구현은 동일하지만 함수와 모듈을 분리하면:
  1. dispatcher 매핑이 mimeType마다 명확하게 보인다
  2. 미래에 Google Docs를 다른 방식(예: docx export)으로 받게 되면 이 파일만 수정
"""
from __future__ import annotations

from langchain_core.documents import Document


def parse_google_doc_text_to_documents(
    file_bytes: bytes,
    metadata: dict | None = None,
) -> list[Document]:
    """
    Args:
        file_bytes: GoogleDriveClient.download_file()이 받은 plain text bytes
                    (Google Docs → 'text/plain' export 결과)
        metadata: Document에 첨부할 메타데이터

    Returns:
        Document 1개를 담은 list
    """
    text = file_bytes.decode("utf-8")
    return [Document(page_content=text, metadata=metadata or {})]

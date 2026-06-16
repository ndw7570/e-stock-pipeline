"""
PDF bytes → LangChain Document 변환 (페이지별).

[메커니즘 설명]
LangChain의 PyPDFLoader는 PDF를 페이지 단위로 잘라 각 페이지를 하나의 Document로
만들어준다. 이는 직접 구현보다 큰 장점이다:
  - 직접 구현: 모든 페이지를 \\n\\n으로 합쳐서 한 덩어리 텍스트
  - LangChain : 페이지마다 별도 Document + metadata['page']에 페이지 번호 자동 추가

이 차이는 검색 단계에서 큰 의미를 가진다. 검색 결과 "이 문장은 보고서 3페이지에서
나왔다"고 명시할 수 있고, 같은 PDF의 다른 페이지가 별개 청크로 인덱싱된다.

[왜 임시 파일을 만드는가?]
PyPDFLoader는 파일 경로(string)를 받는다. Drive에서 받은 bytes를 그대로 넘길
수 없으므로 임시 파일을 만들어 경로를 전달한다. 사용 후 자동 삭제한다.

[try-finally의 이유]
loader.load() 도중 예외가 발생해도 임시 파일을 반드시 삭제하기 위함이다.
이 패턴은 운영 시 디스크 누수를 막는다.
"""
from __future__ import annotations

import os
import tempfile

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


def parse_pdf_to_documents(
    file_bytes: bytes,
    metadata: dict | None = None,
) -> list[Document]:
    """
    Args:
        file_bytes: PDF 파일 raw bytes
        metadata: 각 페이지 Document에 추가될 공통 메타데이터

    Returns:
        페이지별 Document의 list (PDF에 N 페이지면 N개)
    """
    # 1) bytes를 임시 파일에 쓰기
    # delete=False: 컨텍스트 빠져나가도 파일 유지 (loader가 읽어야 함)
    # suffix=".pdf": 일부 라이브러리가 확장자를 보고 파싱 방식 결정
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        # 2) PyPDFLoader 호출 → 페이지별 Document list 반환
        # 각 Document.metadata에는 자동으로 다음이 들어있음:
        #   - source: 임시 파일 경로 (우리에겐 의미 없음, 곧 덮어씀)
        #   - page  : 0부터 시작하는 페이지 번호
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()

        # 3) 사용자 metadata를 각 Document에 병합
        # source는 임시 파일 경로라 의미 없으므로 사용자 metadata로 덮어쓴다.
        for doc in documents:
            doc.metadata.update(metadata or {})

        return documents

    finally:
        # 4) 임시 파일 정리 (예외 발생해도 실행됨)
        os.unlink(tmp_path)

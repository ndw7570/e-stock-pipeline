"""
D3 LangChain 검증 스크립트.

Drive에서 지원 mimeType의 파일 1개를 골라 LangChain Document로 변환 후
구조를 출력한다.

[direct_parse_one_file.py와의 차이]
  - 출력 단위: 직접은 str(텍스트 1덩어리), LangChain은 list[Document]
  - metadata: LangChain은 file_id/file_name/mime_type을 Document에 박아둠
  - PDF: 직접은 1덩어리, LangChain은 페이지별 분리 (큰 차이!)
"""
from app.rag_drive_search.clients.google_drive_client import GoogleDriveClient
from app.rag_drive_search.services.parsers.langchain_dispatcher import (
    PARSER_REGISTRY,
    parse_file_to_documents,
)


def main() -> None:
    client = GoogleDriveClient()

    # 지원 mimeType만 가져오는 query
    supported_types = list(PARSER_REGISTRY.keys())
    query = (
        "trashed = false and ("
        + " or ".join(f"mimeType = '{mt}'" for mt in supported_types)
        + ")"
    )

    files = client.list_files(query=query, page_size=10)
    if not files:
        print("지원 mimeType의 파일이 없습니다.")
        return

    target = files[0]
    print(f"=== 대상 파일 ===")
    print(f"name      : {target['name']}")
    print(f"mimeType  : {target['mimeType']}")
    print()

    print("=== 다운로드 중 ===")
    file_bytes = client.download_file(target["id"], target["mimeType"])
    print(f"받은 bytes: {len(file_bytes):,}")
    print()

    # 인덱싱 시 청크에 박힐 공통 메타데이터를 미리 준비
    # 검색 단계에서 이 필드들로 필터링 가능
    common_metadata = {
        "file_id": target["id"],
        "file_name": target["name"],
        "mime_type": target["mimeType"],
        "modified_time": target.get("modifiedTime", ""),
    }

    print("=== LangChain 파싱 ===")
    documents = parse_file_to_documents(
        file_bytes=file_bytes,
        mime_type=target["mimeType"],
        metadata=common_metadata,
    )
    print(f"Document 개수: {len(documents)}")
    print()

    # 각 Document 구조 출력
    for idx, doc in enumerate(documents):
        print(f"--- Document #{idx} ---")
        print(f"metadata: {doc.metadata}")
        print(f"page_content 길이: {len(doc.page_content):,} 글자")
        print(f"앞 200자: {doc.page_content[:200]}")
        print()


if __name__ == "__main__":
    main()

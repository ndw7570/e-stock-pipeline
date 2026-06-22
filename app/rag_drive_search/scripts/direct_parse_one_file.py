from app.rag_drive_search.clients.google_drive_client import GoogleDriveClient
from app.rag_drive_search.services.parsers.direct_dispatcher import (
    PARSER_REGISTRY,
    parse_file,
)


def main() -> None:
    """
    Drive에서 지원하는 mimeType의 파일 1개를 골라
    다운로드 + 파싱해서 텍스트 앞부분 출력.
    """
    client = GoogleDriveClient()

    # 지원하는 mimeType만 가져오는 query 생성
    supported_types = list(PARSER_REGISTRY.keys())
    query = (
        "trashed = false and ("
        + " or ".join(f"mimeType = '{mt}'" for mt in supported_types)
        + ")"
    )

    files = client.list_files(query=query, page_size=10)
    if not files:
        print("지원하는 mimeType의 파일이 없어요.")
        return

    # 첫 번째 파일로 검증
    target = files[0]
    print(f"=== 대상 파일 ===")
    print(f"name      : {target['name']}")
    print(f"mimeType  : {target['mimeType']}")
    print(f"id        : {target['id']}")
    print()

    print("=== 다운로드 중 ===")
    file_bytes = client.download_file(
        file_id=target["id"],
        mime_type=target["mimeType"],
    )
    print(f"받은 bytes: {len(file_bytes):,}")
    print()

    print("=== 파싱 ===")
    text = parse_file(file_bytes, target["mimeType"])
    print(f"추출된 텍스트 길이: {len(text):,} 글자")
    print()

    print("=== 텍스트 앞 500자 ===")
    print(text[:500])
    print("...")


if __name__ == "__main__":
    main()

from app.rag_drive_search.clients.google_drive_client import GoogleDriveClient


def main() -> None:
    """
    본인 Drive의 파일 목록 100개까지 출력.
    D2 검증용 진입점.
    """
    client = GoogleDriveClient()
    files = client.list_files(page_size=50)

    by_type: dict[str, int] = {}

    print(f"{'idx':>4}  {'mimeType':<48}  {'size':>10}  name")
    print("-" * 120)

    for idx, file in enumerate(files[:100], start=1):
        mime = file.get("mimeType", "?")
        size = file.get("size", "-")
        name = file.get("name", "?")

        by_type[mime] = by_type.get(mime, 0) + 1

        print(f"{idx:>4}  {mime:<48}  {size:>10}  {name}")

    count = min(len(files), 100)
    print("-" * 120)
    print(f"\n총 {count}개 파일\n")
    print("mimeType별 집계:")
    for mime, cnt in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {cnt:>4}  {mime}")


if __name__ == "__main__":
    main()

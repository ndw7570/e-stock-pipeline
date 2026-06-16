def parse_google_doc_text(file_bytes: bytes) -> str:
    """
    Google Docs의 plain text export bytes를 텍스트로 변환.
    GoogleDriveClient.download_file()이 export 이미 처리했으므로 decode만.

    Args:
        file_bytes: download_file()로 받은 bytes (mime_type='text/plain' export 결과)

    Returns:
        utf-8 디코딩된 텍스트
    """
    return file_bytes.decode("utf-8")

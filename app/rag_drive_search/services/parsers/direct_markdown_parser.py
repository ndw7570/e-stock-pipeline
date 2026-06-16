def parse_markdown(file_bytes: bytes) -> str:
    """
    Markdown 파일을 텍스트로 추출.
    Markdown은 이미 plain text라 utf-8 decode만 하면 끝.

    Args:
        file_bytes: Drive에서 받은 raw bytes

    Returns:
        utf-8 디코딩된 텍스트
    """
    return file_bytes.decode("utf-8")

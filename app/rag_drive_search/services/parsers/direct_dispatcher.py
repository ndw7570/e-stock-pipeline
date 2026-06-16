from app.rag_drive_search.services.parsers.markdown_parser import parse_markdown
from app.rag_drive_search.services.parsers.pdf_parser import parse_pdf
from app.rag_drive_search.services.parsers.google_docs_parser import parse_google_doc_text


# mimeType별 파서 매핑.
# 새 mimeType 지원 시 여기에 한 줄 추가하면 됨 (open/closed principle).
PARSER_REGISTRY = {
    "text/markdown": parse_markdown,
    "application/pdf": parse_pdf,
    "application/vnd.google-apps.document": parse_google_doc_text,
}


def parse_file(file_bytes: bytes, mime_type: str) -> str:
    """
    mimeType에 맞는 파서를 골라서 텍스트 추출.

    Args:
        file_bytes: 파일 raw bytes
        mime_type: 파일의 mimeType

    Returns:
        추출된 텍스트

    Raises:
        ValueError: 지원하지 않는 mimeType
    """
    parser = PARSER_REGISTRY.get(mime_type)
    if parser is None:
        raise ValueError(f"Unsupported mime_type: {mime_type}")

    return parser(file_bytes)


def is_supported(mime_type: str) -> bool:
    """mimeType이 지원되는지 체크 (인덱싱 필터링용)."""
    return mime_type in PARSER_REGISTRY

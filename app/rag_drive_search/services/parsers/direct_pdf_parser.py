import io

from pypdf import PdfReader


def parse_pdf(file_bytes: bytes) -> str:
    """
    PDF bytes를 텍스트로 추출.
    페이지별로 텍스트 뽑아서 \\n\\n으로 합침.

    Args:
        file_bytes: PDF 파일 raw bytes

    Returns:
        모든 페이지의 텍스트가 합쳐진 문자열
    """
    buffer = io.BytesIO(file_bytes)
    reader = PdfReader(buffer)

    pages_text = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages_text.append(text)

    return "\n\n".join(pages_text)

from __future__ import annotations


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 100,
) -> list[str]:
    """
    텍스트를 단락 우선 + 글자 단위로 청킹.

    전략:
    1. \\n\\n으로 단락 분리
    2. 단락들을 누적하다가 chunk_size 넘으면 새 청크 시작
    3. 각 청크 끝부분 overlap만큼을 다음 청크 앞에 붙여 맥락 보존

    Args:
        text: 추출된 전체 텍스트
        chunk_size: 한 청크의 최대 글자 수 (목표값, 단락 경계에서 자르려고 살짝 넘을 수 있음)
        overlap: 청크 사이 겹치는 글자 수

    Returns:
        청크 문자열의 list
    """
    if not text.strip():
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)

        # 단락 하나가 chunk_size보다 크면 글자 단위 강제 분할
        if para_len > chunk_size:
            # 현재 누적분 먼저 flush
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_len = 0

            # 큰 단락을 chunk_size - overlap 간격으로 슬라이스 (overlap 만큼 겹침)
            stride = chunk_size - overlap
            for i in range(0, para_len, stride):
                chunks.append(para[i : i + chunk_size])
            continue

        # 현재 청크에 단락 추가 시 chunk_size 초과하면 flush
        if current_len + para_len + 2 > chunk_size and current:
            chunks.append("\n\n".join(current))

            # overlap: 직전 청크의 마지막 overlap 글자를 새 청크 앞에 둠
            tail = chunks[-1][-overlap:] if overlap > 0 else ""
            current = [tail] if tail else []
            current_len = len(tail)

        current.append(para)
        current_len += para_len + 2  # +2는 "\n\n" 길이

    # 마지막 누적분 flush
    if current:
        chunks.append("\n\n".join(current))

    return chunks

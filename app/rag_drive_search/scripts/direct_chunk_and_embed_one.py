from app.rag_drive_search.clients.google_drive_client import GoogleDriveClient
from app.rag_drive_search.services.parsers.direct_dispatcher import (
    PARSER_REGISTRY,
    parse_file,
)
from app.rag_drive_search.services.chunking.direct_text_chunker import chunk_text
from app.rag_drive_search.services.embedding.direct_sentence_transformer_embedder import (
    SentenceTransformerEmbedder,
)


def main() -> None:
    """
    Drive에서 파일 1개 가져와 텍스트 추출 → 청킹 → 임베딩까지 한 번에.
    """
    client = GoogleDriveClient()

    supported_types = list(PARSER_REGISTRY.keys())
    query = (
        "trashed = false and ("
        + " or ".join(f"mimeType = '{mt}'" for mt in supported_types)
        + ")"
    )

    files = client.list_files(query=query, page_size=10)
    if not files:
        print("지원하는 파일이 없습니다.")
        return

    target = files[0]
    print(f"=== 대상 파일 ===")
    print(f"name      : {target['name']}")
    print(f"mimeType  : {target['mimeType']}")
    print()

    # 1) 다운로드
    file_bytes = client.download_file(target["id"], target["mimeType"])
    print(f"다운로드 bytes: {len(file_bytes):,}")

    # 2) 파싱
    text = parse_file(file_bytes, target["mimeType"])
    print(f"추출 텍스트   : {len(text):,} 글자")
    print()

    # 3) 청킹
    chunks = chunk_text(text, chunk_size=1000, overlap=100)
    print(f"=== 청킹 결과 ===")
    print(f"청크 수       : {len(chunks)}")
    if chunks:
        lengths = [len(c) for c in chunks]
        print(f"청크 길이     : min={min(lengths)}, max={max(lengths)}, avg={sum(lengths)//len(lengths)}")
    print()

    if not chunks:
        print("청크가 없어 임베딩 생략.")
        return

    # 4) 임베딩 (첫 실행 시 모델 다운로드 ~90MB)
    print("=== 임베딩 모델 로드 중... (첫 실행은 다운로드 포함 1~2분) ===")
    embedder = SentenceTransformerEmbedder()
    print(f"모델          : {embedder.model_name}")
    print(f"벡터 차원     : {embedder.dimension}")
    print()

    embeddings = embedder.embed(chunks)
    print(f"=== 임베딩 결과 ===")
    print(f"벡터 개수     : {len(embeddings)}")
    print(f"각 벡터 차원  : {len(embeddings[0])}")
    print()

    # 첫 청크와 그 벡터 미리보기
    print("=== 첫 청크 ===")
    print(chunks[0][:200], "..." if len(chunks[0]) > 200 else "")
    print()
    print("=== 첫 청크의 벡터 (앞 5개 차원만) ===")
    print(embeddings[0][:5])


if __name__ == "__main__":
    main()

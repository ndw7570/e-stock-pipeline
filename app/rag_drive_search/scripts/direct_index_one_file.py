"""
D5 direct 검증 — Drive에서 파일 1개 → 파싱 → 청킹 → 임베딩 → ChromaDB 저장.

전체 파이프라인 한 번에 검증.
"""
from app.rag_drive_search.clients.google_drive_client import GoogleDriveClient
from app.rag_drive_search.services.parsers.direct_dispatcher import (
    PARSER_REGISTRY,
    parse_file,
)
from app.rag_drive_search.services.chunking.direct_text_chunker import chunk_text
from app.rag_drive_search.services.embedding.direct_sentence_transformer_embedder import (
    SentenceTransformerEmbedder,
)
from app.rag_drive_search.services.vectorstore.direct_chroma_store import (
    DirectChromaStore,
)


def main() -> None:
    client = GoogleDriveClient()
    embedder = SentenceTransformerEmbedder()
    store = DirectChromaStore()

    # 지원 mimeType만
    supported_types = list(PARSER_REGISTRY.keys())
    query = (
        "trashed = false and ("
        + " or ".join(f"mimeType = '{mt}'" for mt in supported_types)
        + ")"
    )

    files = client.list_files(query=query, page_size=10)
    if not files:
        print("지원 파일 없음")
        return

    target = files[0]
    print(f"=== 대상 파일 ===")
    print(f"name      : {target['name']}")
    print(f"mimeType  : {target['mimeType']}")
    print()

    # 1) 다운로드 + 파싱
    file_bytes = client.download_file(target["id"], target["mimeType"])
    text = parse_file(file_bytes, target["mimeType"])
    print(f"텍스트   : {len(text):,} 글자")

    # 2) 청킹
    chunks = chunk_text(text, chunk_size=1000, overlap=100)
    print(f"청크 수  : {len(chunks)}")

    # 3) 임베딩
    embeddings = embedder.embed(chunks)
    print(f"벡터 수  : {len(embeddings)}")

    # 4) ChromaDB upsert
    file_metadata = {
        "file_id": target["id"],
        "file_name": target["name"],
        "mime_type": target["mimeType"],
        "modified_time": target.get("modifiedTime", ""),
    }
    saved = store.upsert_chunks(
        file_id=target["id"],
        chunks=chunks,
        embeddings=embeddings,
        file_metadata=file_metadata,
    )
    print(f"ChromaDB 저장: {saved}개 청크")
    print()

    # 5) 컬렉션 전체 상태
    total = store.count()
    print(f"=== 컬렉션 전체 청크 수: {total} ===")


if __name__ == "__main__":
    main()

"""
D5 LangChain 인덱싱 — Drive → 파싱(D3) → 청킹(D4) → ChromaDB 저장.

[direct vs langchain 차이]
  - direct  : 텍스트(str) 흐름. 사용자가 임베딩 직접 호출 후 ChromaDB에 ids/embeddings/...
  - langchain: Document 흐름. add_documents() 한 번에 임베딩+저장.

LangChain 흐름은 컴포넌트 간 wiring이 더 짧고 명시적이다.
"""
from app.rag_drive_search.clients.google_drive_client import GoogleDriveClient
from app.rag_drive_search.services.parsers.langchain_dispatcher import (
    PARSER_REGISTRY,
    parse_file_to_documents,
)
from app.rag_drive_search.services.chunking.langchain_text_chunker import (
    chunk_documents,
)
from app.rag_drive_search.services.embedding.langchain_sentence_transformer_embedder import (
    create_embeddings,
)
from app.rag_drive_search.services.vectorstore.langchain_chroma_store import (
    LangchainChromaStore,
)


def main() -> None:
    client = GoogleDriveClient()
    embeddings = create_embeddings()
    store = LangchainChromaStore(embeddings=embeddings)

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

    # 1) 다운로드
    file_bytes = client.download_file(target["id"], target["mimeType"])

    # 2) 파싱 → Document list (D3 langchain)
    common_metadata = {
        "file_id": target["id"],
        "file_name": target["name"],
        "mime_type": target["mimeType"],
        "modified_time": target.get("modifiedTime", ""),
    }
    documents = parse_file_to_documents(file_bytes, target["mimeType"], common_metadata)
    print(f"파싱 Document  : {len(documents)}개")

    # 3) 청킹 (D4 langchain) → Document list
    chunked_docs = chunk_documents(documents, chunk_size=1000, chunk_overlap=100)
    print(f"청킹 Document  : {len(chunked_docs)}개")

    # 4) ChromaDB upsert (D5 langchain) — 임베딩 자동
    saved = store.upsert_documents(
        file_id=target["id"],
        chunked_documents=chunked_docs,
    )
    print(f"ChromaDB 저장   : {saved}개 청크")
    print()

    # 5) 컬렉션 상태
    total = store.count()
    print(f"=== 컬렉션 'drive_chunks_langchain' 전체 청크: {total} ===")


if __name__ == "__main__":
    main()

"""
D5 LangChain 검색 — query 문자열 → 자동 임베딩 → 유사 Document 검색.

[direct vs langchain 차이]
  - direct  : embedder.embed([query])[0] 직접 호출 → collection.query(embeddings, ...)
  - langchain: store.search(query=문자열, k=5) 한 줄 (임베딩 자동)
"""
from app.rag_drive_search.services.embedding.langchain_sentence_transformer_embedder import (
    create_embeddings,
)
from app.rag_drive_search.services.vectorstore.langchain_chroma_store import (
    LangchainChromaStore,
)


QUERY = "성장 에이전트 구조 세팅 방향"


def main() -> None:
    embeddings = create_embeddings()
    store = LangchainChromaStore(embeddings=embeddings)

    print(f"=== 컬렉션 청크 수: {store.count()} ===")
    print(f"=== 쿼리: '{QUERY}' ===")
    print()

    # similarity_search_with_score: (Document, distance) 튜플 list
    results = store.search(query=QUERY, k=5)

    for rank, (doc, distance) in enumerate(results, start=1):
        print(f"=== Rank #{rank} (distance={distance:.4f}) ===")
        print(f"file       : {doc.metadata.get('file_name')}")
        print(f"chunk_idx  : {doc.metadata.get('chunk_idx', '?')}")
        print(f"start_index: {doc.metadata.get('start_index', '?')}")
        print(f"text       : {doc.page_content[:200]}{'...' if len(doc.page_content) > 200 else ''}")
        print()


if __name__ == "__main__":
    main()

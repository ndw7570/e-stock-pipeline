"""
D5 direct — 저장된 벡터로 검색 동작 확인.

쿼리 문장 → 임베딩 → ChromaDB query → top-5 청크 출력.
"""
from app.rag_drive_search.services.embedding.direct_sentence_transformer_embedder import (
    SentenceTransformerEmbedder,
)
from app.rag_drive_search.services.vectorstore.direct_chroma_store import (
    DirectChromaStore,
)


# 검색 쿼리 — 인덱싱된 문서에 따라 적절히 수정해서 테스트
QUERY = "성장 에이전트 구조 세팅 방향"


def main() -> None:
    embedder = SentenceTransformerEmbedder()
    store = DirectChromaStore()

    print(f"=== 컬렉션 현재 청크 수: {store.count()} ===")
    print(f"=== 쿼리: '{QUERY}' ===")
    print()

    # 쿼리도 같은 임베딩 모델로 벡터화 (검색 정확도의 핵심)
    query_embedding = embedder.embed([QUERY])[0]

    results = store.search(query_embedding=query_embedding, n_results=5)

    # ChromaDB 결과 구조: 각 필드가 [[...]] (외부 list = 쿼리당)
    ids = results["ids"][0]
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    for rank, (cid, doc, meta, dist) in enumerate(zip(ids, docs, metas, dists), start=1):
        print(f"=== Rank #{rank} (distance={dist:.4f}) ===")
        print(f"id       : {cid}")
        print(f"file     : {meta.get('file_name')}")
        print(f"chunk_idx: {meta.get('chunk_idx')}")
        print(f"text     : {doc[:200]}{'...' if len(doc) > 200 else ''}")
        print()


if __name__ == "__main__":
    main()

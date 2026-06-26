"""
LangChain의 Chroma vector store 래퍼.

[메커니즘 설명]
LangChain의 `Chroma`는 ChromaDB Python SDK를 한 단계 더 추상화한다.
가장 큰 차이:
  - direct  : 사용자가 임베딩 → ids/embeddings/documents/metadatas 따로 전달
  - langchain: Document list만 주면 임베딩까지 자동 (embedding_function 등록 덕)

[embedding_function]
Chroma 생성 시 `embedding_function=embeddings`로 등록하면, add_documents()
호출 시 LangChain이 자동으로 임베딩을 수행해서 ChromaDB에 저장한다.
검색 시 similarity_search(query) 호출 시에도 query를 자동 임베딩 후 검색.

[Collection 분리]
direct 버전과 같은 컬렉션을 공유할 수도 있지만, 학습 비교 목적상 별도 컬렉션
('drive_chunks_langchain')으로 분리한다. 같은 persist_path 안에 여러 컬렉션 공존 가능.

[ID 명시]
LangChain은 ID 미지정 시 UUID 자동 생성. 그러면 같은 파일 재인덱싱 시 중복 발생.
우리는 direct와 같은 ID 패턴 (f"{file_id}_{idx}") 명시해서 upsert idempotent 유지.
"""
from __future__ import annotations

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings


COLLECTION_NAME = "drive_chunks_langchain"


class LangchainChromaStore:
    """
    LangChain Chroma vector store 래퍼.

    역할:
    - Chroma 인스턴스 생성 (embedding_function 등록)
    - Document list upsert (임베딩 자동)
    - similarity_search로 Document list 검색
    """

    def __init__(
        self,
        embeddings: Embeddings,
        persist_path: str = "/opt/airflow/chroma_data",
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        self.embeddings = embeddings
        # LangChain Chroma:
        # - collection_name : direct와 분리하기 위해 다른 이름
        # - embedding_function: add/search 시 자동 임베딩
        # - persist_directory: 로컬 영구 저장 경로 (PersistentClient 내부 사용)
        # - collection_metadata: HNSW 거리 메트릭 등 (cosine 권장)
        self.vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=persist_path,
            collection_metadata={"hnsw:space": "cosine"},
        )

    def upsert_documents(
        self,
        file_id: str,
        chunked_documents: list[Document],
    ) -> int:
        """
        D4 langchain의 청크 Document list를 vector store에 upsert.

        Args:
            file_id: 파일 ID (청크 ID 생성)
            chunked_documents: chunk_documents()가 반환한 Document list

        Returns:
            저장된 청크 수
        """
        if not chunked_documents:
            return 0

        # 청크 ID 명시 → 재인덱싱 시 자동 덮어쓰기 (idempotent)
        # direct 버전과 동일한 패턴
        ids = [f"{file_id}_{idx}" for idx in range(len(chunked_documents))]

        # add_documents: Document list 받아 내부적으로:
        #   1. 각 Document.page_content를 embedding_function으로 벡터화
        #   2. 같은 ID 있으면 덮어쓰기, 없으면 추가
        #   3. metadata와 함께 저장
        # → direct 버전의 collection.upsert()와 동일한 결과
        self.vector_store.add_documents(documents=chunked_documents, ids=ids)
        return len(chunked_documents)

    def search(
        self,
        query: str,
        k: int = 5,
        filter: dict | None = None,
    ) -> list[tuple[Document, float]]:
        """
        쿼리 문자열로 vector search (임베딩 자동).

        Args:
            query: 검색할 문장 (텍스트 그대로)
            k: top-k
            filter: metadata 필터 (예: {"mime_type": "application/pdf"})

        Returns:
            (Document, distance) 튜플의 list. distance 0에 가까울수록 유사.

        [direct vs langchain 차이]
            direct  : query_embedding 벡터를 미리 만들어서 전달
            langchain: query 문자열 그대로. 내부적으로 임베딩.
        """
        # similarity_search_with_score: Document + distance 같이 반환
        # (similarity_search는 distance 안 줌)
        return self.vector_store.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter,
        )

    def count(self) -> int:
        """컬렉션의 현재 청크 수 (내부 chromadb collection 접근)."""
        # LangChain Chroma는 .collection 속성으로 raw ChromaDB collection 노출
        return self.vector_store._collection.count()

    def delete_by_file(self, file_id: str) -> None:
        """특정 파일의 모든 청크 삭제."""
        # _collection으로 raw API 호출 (LangChain이 delete 메서드 미제공)
        self.vector_store._collection.delete(where={"file_id": file_id})

"""
ChromaDB Python SDK 직접 사용 (LangChain X).

[메커니즘 설명]
ChromaDB는 RAG 전용 벡터 데이터베이스다. 핵심 API는 단 두 개:
  - collection.upsert(ids, embeddings, documents, metadatas)
  - collection.query(query_embeddings, n_results, where)

[Collection 개념]
RDB의 "테이블"에 해당. 같은 임베딩 모델/차원의 벡터들을 묶는 단위.
우리 프로젝트는 'drive_chunks' 컬렉션 하나로 충분.

[ID 설계]
청크 ID = f"{file_id}_{chunk_idx}"
이렇게 하면 같은 파일을 다시 인덱싱해도 같은 ID가 생성되어
upsert가 idempotent (덮어쓰기) 작동. 중복 청크가 쌓이지 않음.

[Distance Metric]
collection 생성 시 'hnsw:space' 옵션으로 거리 메트릭 지정.
sentence-transformers 임베딩은 보통 'cosine' (코사인 유사도)를 권장.
한 번 정하면 변경 어려움 (재인덱싱 필요).

[Metadata]
ChromaDB metadata 값은 str/int/float/bool만 가능 (list/dict 불가).
검색 시 where={"mime_type": "application/pdf"} 같은 필터링에 사용.
"""
from __future__ import annotations

from typing import Any

import chromadb


COLLECTION_NAME = "drive_chunks"


class DirectChromaStore:
    """
    ChromaDB Python SDK를 직접 호출하는 래퍼.

    역할:
    - PersistentClient 생성 (로컬 디스크 저장)
    - Collection 생성/조회 (자동)
    - 청크 upsert / 검색 메서드 제공

    이 클래스는 임베딩을 모른다. 호출자가 벡터를 미리 만들어서 전달.
    """

    def __init__(
        self,
        persist_path: str = "/opt/airflow/chroma_data",
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        # PersistentClient: 로컬 디스크에 SQLite + 벡터 인덱스 저장.
        # 같은 path로 재실행하면 기존 데이터 그대로 로드.
        self.client = chromadb.PersistentClient(path=persist_path)

        # get_or_create_collection: 있으면 가져오고 없으면 만듦 (idempotent)
        # metadata "hnsw:space": cosine → 코사인 유사도 사용 (벡터 정규화된 모델에 적합)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_chunks(
        self,
        file_id: str,
        chunks: list[str],
        embeddings: list[list[float]],
        file_metadata: dict[str, Any],
    ) -> int:
        """
        한 파일의 청크들을 ChromaDB에 upsert.

        Args:
            file_id: Drive 파일 ID (청크 ID 생성에 사용)
            chunks: 청크 텍스트 list
            embeddings: 청크별 벡터 (chunks와 길이 동일)
            file_metadata: 파일 공통 메타 (file_name, mime_type 등)

        Returns:
            저장된 청크 수
        """
        if not chunks:
            return 0

        # 청크별 고유 ID: file_id + chunk_idx → idempotent
        ids = [f"{file_id}_{idx}" for idx in range(len(chunks))]

        # 각 청크 metadata: 파일 공통 메타 + chunk_idx
        # ChromaDB metadata는 dict의 값이 str/int/float/bool만 허용
        metadatas = [
            {**file_metadata, "chunk_idx": idx}
            for idx in range(len(chunks))
        ]

        # upsert: 같은 ID가 있으면 덮어쓰기, 없으면 새로 추가
        # → 같은 파일 재인덱싱해도 중복 X
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )

        return len(chunks)

    def search(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        where: dict | None = None,
    ) -> dict:
        """
        벡터 유사도 검색.

        Args:
            query_embedding: 검색 쿼리의 임베딩 벡터
            n_results: top-k
            where: metadata 필터 (예: {"mime_type": "application/pdf"})

        Returns:
            ChromaDB 검색 결과 dict.
            구조: {
                "ids":       [[id1, id2, ...]],          ← 외부 list는 batch (쿼리당)
                "documents": [["청크 텍스트", ...]],
                "metadatas": [[{...}, ...]],
                "distances": [[0.12, 0.18, ...]],         ← 0에 가까울수록 비슷함
            }
        """
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )

    def count(self) -> int:
        """현재 컬렉션의 청크 총 개수."""
        return self.collection.count()

    def delete_by_file(self, file_id: str) -> None:
        """특정 파일의 모든 청크 삭제 (재인덱싱 전 청소용)."""
        # where 필터로 metadata 매칭되는 청크들 삭제
        self.collection.delete(where={"file_id": file_id})

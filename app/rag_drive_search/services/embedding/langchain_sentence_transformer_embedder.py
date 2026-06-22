"""
LangChain의 HuggingFaceEmbeddings로 텍스트 → 벡터.

[메커니즘 설명]
LangChain의 HuggingFaceEmbeddings는 내부적으로 sentence-transformers를 사용한다.
즉 direct 구현의 SentenceTransformerEmbedder와 동일한 모델, 동일한 벡터 결과.
다른 점은 LangChain Embeddings 인터페이스를 따른다는 것이다.

[Embeddings 인터페이스의 두 메서드]
  embed_documents(texts: list[str]) -> list[list[float]]
    → 여러 문서/청크를 한 번에 벡터화. 인덱싱 시 사용.
  embed_query(text: str) -> list[float]
    → 쿼리 1개를 벡터화. 검색 시 사용.

왜 두 메서드로 분리?
일부 모델은 "문서 인코딩"과 "쿼리 인코딩"을 다르게 한다 (예: asymmetric search).
all-MiniLM은 대칭 모델이라 둘이 같지만, 인터페이스로 분리해두면 모델 교체 시 안전.

[VectorStore와의 통합]
LangChain의 Chroma vector store는 이 Embeddings 객체를 받는다:
  vector_store = Chroma(embedding_function=embeddings)
이러면 vector_store.add_documents() 호출 시 자동으로 임베딩이 수행된다.
직접 임베딩 → DB 저장의 두 단계를 한 번에 호출하게 해주는 추상화.
"""
from __future__ import annotations

from langchain_huggingface import HuggingFaceEmbeddings


DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def create_embeddings(
    model_name: str = DEFAULT_MODEL_NAME,
) -> HuggingFaceEmbeddings:
    """
    HuggingFaceEmbeddings 인스턴스 생성.

    Args:
        model_name: HuggingFace Hub의 모델 이름

    Returns:
        HuggingFaceEmbeddings 객체.
        - embed_documents(texts) : 여러 청크 벡터화
        - embed_query(text)      : 단일 쿼리 벡터화
        - 내부적으로 sentence-transformers 사용 (direct 구현과 같은 모델)
    """
    # model_kwargs: sentence-transformers 모델 생성 시 옵션
    # encode_kwargs: encode() 호출 시 옵션
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},          # CPU 사용 (GPU 없는 환경)
        encode_kwargs={"normalize_embeddings": True},  # 코사인 유사도와 잘 맞도록 정규화
    )

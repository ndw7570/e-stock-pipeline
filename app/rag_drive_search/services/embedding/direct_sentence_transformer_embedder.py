from __future__ import annotations

from sentence_transformers import SentenceTransformer


# all-MiniLM-L6-v2: 가볍고 빠른 다국어 임베딩 모델
# - 384차원 벡터
# - CPU에서도 충분히 빠름
# - 90MB 정도
DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class SentenceTransformerEmbedder:
    """
    sentence-transformers 기반 임베딩 클라이언트.

    역할:
    - 모델 1회 로드 (생성자) → 여러 번 재사용
    - 텍스트 리스트 → 벡터 리스트 변환

    이 클래스는 Drive/파싱/DB를 모른다.
    오직 텍스트 → 벡터 변환만 담당.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        self.model_name = model_name
        # 첫 호출 시 모델 다운로드 (약 90MB). 이후엔 캐시 사용.
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        텍스트 list → 벡터 list 변환.

        Args:
            texts: 텍스트 문자열 list. 빈 list면 빈 list 반환.

        Returns:
            각 텍스트에 대응하는 벡터 list.
            len(returned) == len(texts), 각 벡터 길이 == self.dimension
        """
        if not texts:
            return []

        # convert_to_numpy=True → numpy ndarray로 반환 (빠름)
        # show_progress_bar=False → 학습용엔 progress bar 끄기
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            batch_size=32,
        )

        # numpy → 일반 list (pgvector 저장 시 호환성 좋음)
        return embeddings.tolist()

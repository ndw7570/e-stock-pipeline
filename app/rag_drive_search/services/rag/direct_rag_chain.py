"""
LLM-agnostic RAG Chain (LangChain X).

[메커니즘 설명 — RAG의 4단계]
RAG (Retrieval-Augmented Generation):
  1. Retrieve : 질문과 의미상 비슷한 문서 청크 검색 (D5 ChromaDB)
  2. Augment  : 검색된 청크들을 LLM 프롬프트의 "context"로 주입
  3. Generate : LLM이 context + 질문을 보고 답변 생성
  4. Cite     : 어느 청크에서 나왔는지 출처 명시

[왜 LLM 주입?]
- 이 클래스는 어떤 LLM인지(Gemini/GPT/Claude) 알 필요 없음.
- 호출자가 LLM 클라이언트를 만들어서 넘기면, 우리는 .generate(prompt) 만 호출.
- → 모델 교체 시 RAG 코드 0줄 수정. 새 LLM 추가도 새 클라이언트 한 파일.
- → "단일 책임 원칙 (SRP)" + "의존성 주입 (DI)".

[프롬프트 디자인 핵심]
- system 역할 명시 ("문서 기반 Q&A 어시스턴트")
- context 구분자 명확 (--- 등)
- 모르면 모른다고 답해 (환각 방지)
- 출처 인용 강제 (검증 가능성)
"""
from __future__ import annotations

from app.rag_drive_search.services.embedding.direct_sentence_transformer_embedder import (
    SentenceTransformerEmbedder,
)
from app.rag_drive_search.services.llms.base import LLMClient
from app.rag_drive_search.services.vectorstore.direct_chroma_store import (
    DirectChromaStore,
)


# RAG 프롬프트 템플릿.
# {context}: 검색된 청크들을 합친 텍스트 ([#1], [#2], ... 번호 매김)
# {question}: 사용자 질문
RAG_PROMPT_TEMPLATE = """너는 사내 문서 기반 Q&A 어시스턴트야.
아래 [참고 문서]만 활용해서 [질문]에 답해.

규칙:
- 참고 문서에 없는 내용은 "문서에서 찾을 수 없습니다"라고 답할 것.
- 답변에 사용한 청크 번호를 [출처: #1, #3] 형식으로 명시할 것.
- 답변은 한국어로, 간결하게.

[참고 문서]
{context}

[질문]
{question}

[답변]
"""


class DirectRagChain:
    """
    검색 → 프롬프트 조립 → LLM 호출 RAG Chain.

    이 클래스는 LLM 종류를 모른다.
    LLMClient Protocol을 따르는 객체면 무엇이든 주입 가능 (Gemini/GPT/Claude/...).
    """

    def __init__(
        self,
        llm: LLMClient,
        embedder: SentenceTransformerEmbedder | None = None,
        store: DirectChromaStore | None = None,
    ) -> None:
        # LLM은 외부에서 주입 — 이 Chain은 호출만 함
        self.llm = llm
        # Embedder/Store는 기본값 있음 (호출자 편의)
        self.embedder = embedder or SentenceTransformerEmbedder()
        self.store = store or DirectChromaStore()

    def query(self, question: str, k: int = 5) -> dict:
        """
        RAG 풀 파이프라인 실행.

        Args:
            question: 사용자 질문
            k: 검색할 top-k 청크 수

        Returns:
            {
                "answer": LLM 답변 텍스트,
                "sources": [{"rank", "chunk_id", "file_name", "chunk_idx", "distance", "text"}, ...],
                "model": 사용한 LLM 모델 이름 (llm.model_name),
            }
        """
        # 1) 질문 임베딩 — 인덱싱과 같은 모델 사용 (검색 정확도의 핵심)
        query_embedding = self.embedder.embed([question])[0]

        # 2) ChromaDB top-k 검색
        results = self.store.search(query_embedding=query_embedding, n_results=k)

        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]

        # 3) 검색 결과를 "context"로 조립
        # [#N] 번호 + (출처: 파일명) + 본문 형태
        # → LLM이 출처 인용하기 쉬워짐
        context_parts = []
        for idx, (doc, meta) in enumerate(zip(docs, metas), start=1):
            file_name = meta.get("file_name", "unknown")
            context_parts.append(f"[#{idx}] (출처: {file_name})\n{doc}")
        context = "\n\n---\n\n".join(context_parts)

        # 4) 프롬프트 조립
        prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=question)

        # 5) LLM 호출 — Gemini/GPT/Claude 무엇이든 같은 인터페이스
        answer = self.llm.generate(prompt)

        # 6) 결과 구조화 (출처 추적용)
        sources = [
            {
                "rank": idx,
                "chunk_id": cid,
                "file_name": meta.get("file_name"),
                "chunk_idx": meta.get("chunk_idx"),
                "distance": dist,
                "text": doc[:200],
            }
            for idx, (cid, doc, meta, dist) in enumerate(
                zip(ids, docs, metas, dists), start=1
            )
        ]

        return {
            "answer": answer,
            "sources": sources,
            "model": self.llm.model_name,
        }

"""
D6 direct 검증 — 질문 1개 → RAG → 답변 + 출처.

[변경 핵심 — LLM을 외부에서 주입]
- 이전: DirectRagChain()이 Gemini 자동 생성
- 지금: 사용자가 LLM 클라이언트를 만들어서 chain에 주입
  → 한 줄만 바꿔서 Gemini ↔ GPT 전환 가능
"""
from app.rag_drive_search.services.llms.direct_gemini_client import DirectGeminiClient
# from app.rag_drive_search.services.llms.direct_openai_client import DirectOpenAIClient  # ← GPT 쓸 때 주석 해제
from app.rag_drive_search.services.rag.direct_rag_chain import DirectRagChain


# 인덱싱된 문서 내용에 맞게 질문 수정 (decisions.md 기준 예시)
# QUESTION = "성장 에이전트 구조 세팅 방향은 어떻게 결정됐어?"
QUESTION = "MDM DB 기반 입/퇴사자 시트를 어떻게 하겠대?"

def main() -> None:
    print(f"=== 질문 ===")
    print(QUESTION)
    print()

    # 1) LLM 선택 — 한 줄 바꾸면 Gemini ↔ GPT 전환
    llm = DirectGeminiClient()
    # llm = DirectOpenAIClient()   # ← GPT로 갈 때

    # 2) RAG Chain에 LLM 주입
    chain = DirectRagChain(llm=llm)

    # 3) 질의
    print("=== RAG 실행 중 (검색 → LLM 호출) ===")
    result = chain.query(QUESTION, k=5)
    print()

    # 4) 결과 출력
    print(f"=== 모델: {result['model']} ===")
    print()
    print("=== 답변 ===")
    print(result["answer"])
    print()

    print("=== 출처 (top-5 검색 청크) ===")
    for src in result["sources"]:
        print(f"  #{src['rank']}  distance={src['distance']:.3f}  "
              f"{src['file_name']} (chunk #{src['chunk_idx']})")
        print(f"    → {src['text'][:120]}{'...' if len(src['text']) > 120 else ''}")
        print()


if __name__ == "__main__":
    main()

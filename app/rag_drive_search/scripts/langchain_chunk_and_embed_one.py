"""
D4 LangChain 검증 스크립트.

Drive에서 파일 1개 → LangChain Document → 청킹(Document) → 임베딩(벡터).

[direct 버전과의 차이]
  direct  : Drive → bytes → str → list[str] (청크) → list[list[float]]
  langchain: Drive → bytes → list[Document] → list[Document] (청크) → list[list[float]]

LangChain 버전은 Document 단위로 metadata가 자동 흐른다.
청크에도 file_id, file_name 등이 박혀있어 D5 (ChromaDB 저장) 시 즉시 사용 가능.
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


def main() -> None:
    client = GoogleDriveClient()

    # 지원 mimeType만
    supported_types = list(PARSER_REGISTRY.keys())
    query = (
        "trashed = false and ("
        + " or ".join(f"mimeType = '{mt}'" for mt in supported_types)
        + ")"
    )

    files = client.list_files(query=query, page_size=10)
    if not files:
        print("지원 파일이 없습니다.")
        return

    target = files[0]
    print(f"=== 대상 파일 ===")
    print(f"name      : {target['name']}")
    print(f"mimeType  : {target['mimeType']}")
    print()

    # 1) 다운로드
    file_bytes = client.download_file(target["id"], target["mimeType"])
    print(f"다운로드 bytes: {len(file_bytes):,}")

    # 2) 파싱 (D3 langchain)
    common_metadata = {
        "file_id": target["id"],
        "file_name": target["name"],
        "mime_type": target["mimeType"],
        "modified_time": target.get("modifiedTime", ""),
    }
    documents = parse_file_to_documents(file_bytes, target["mimeType"], common_metadata)
    print(f"파싱 Document  : {len(documents)}개")
    print()

    # 3) 청킹 (D4 langchain) — Document → Document
    chunked_docs = chunk_documents(documents, chunk_size=1000, chunk_overlap=100)
    print(f"=== 청킹 결과 ===")
    print(f"청크 Document  : {len(chunked_docs)}개")
    if chunked_docs:
        lengths = [len(d.page_content) for d in chunked_docs]
        print(f"청크 길이      : min={min(lengths)}, max={max(lengths)}, avg={sum(lengths)//len(lengths)}")
        print(f"첫 청크 metadata: {chunked_docs[0].metadata}")
        print(f"           → start_index가 자동 추가됨에 주목!")
    print()

    if not chunked_docs:
        return

    # 4) 임베딩 (D4 langchain)
    print("=== HuggingFaceEmbeddings 로드 중... ===")
    embeddings = create_embeddings()
    print()

    # Document.page_content만 추출해서 임베딩
    texts = [doc.page_content for doc in chunked_docs]
    vectors = embeddings.embed_documents(texts)
    print(f"=== 임베딩 결과 ===")
    print(f"벡터 개수     : {len(vectors)}")
    print(f"각 벡터 차원  : {len(vectors[0])}")
    print()

    # 미리보기
    print("=== 첫 청크 ===")
    print(chunked_docs[0].page_content[:200], "..." if len(chunked_docs[0].page_content) > 200 else "")
    print()
    print("=== 첫 청크 벡터 (앞 5개 차원) ===")
    print(vectors[0][:5])


if __name__ == "__main__":
    main()

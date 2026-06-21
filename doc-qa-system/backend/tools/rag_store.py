from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
_stores: dict[str, InMemoryVectorStore] = {}


def index_pdf(file_path: str, pages: list[dict]) -> int:
    docs = [
        Document(
            page_content=p["text"].strip(),
            metadata={"page": p["page_number"], "file_path": file_path},
        )
        for p in pages
        if p.get("text", "").strip()
    ]
    if not docs:
        return 0
    _stores[file_path] = InMemoryVectorStore.from_documents(docs, _embeddings)
    return len(docs)


def rag_search(file_path: str, query: str, k: int = 5) -> list[dict]:
    store = _stores.get(file_path)
    if not store:
        return []
    results = store.similarity_search(query, k=k)
    return [
        {"page": r.metadata["page"], "text": r.page_content[:800]}
        for r in results
    ]


def is_indexed(file_path: str) -> bool:
    return file_path in _stores

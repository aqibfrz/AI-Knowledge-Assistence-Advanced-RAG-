from __future__ import annotations

import os
from typing import List, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from .config import settings
from .schemas import Citation


class RAGStore:
    def __init__(self) -> None:
        self.embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=900,
            chunk_overlap=150,
        )
        self.vectorstore: FAISS | None = None
        self.total_documents = 0
        self.total_chunks = 0
        os.makedirs(os.path.dirname(settings.vector_store_path), exist_ok=True)
        self._load_if_exists()

    def _load_if_exists(self) -> None:
        if os.path.exists(settings.vector_store_path):
            self.vectorstore = FAISS.load_local(
                settings.vector_store_path,
                self.embeddings,
                allow_dangerous_deserialization=True,
            )

    def _save(self) -> None:
        if self.vectorstore:
            self.vectorstore.save_local(settings.vector_store_path)

    def add_text(self, text: str, source_name: str) -> int:
        chunks = self.text_splitter.split_text(text)
        docs = [
            Document(
                page_content=chunk,
                metadata={"source": source_name, "chunk_id": f"{source_name}:{i}"},
            )
            for i, chunk in enumerate(chunks)
        ]
        if not docs:
            return 0

        if self.vectorstore is None:
            self.vectorstore = FAISS.from_documents(docs, self.embeddings)
        else:
            self.vectorstore.add_documents(docs)
        self.total_documents += 1
        self.total_chunks += len(docs)
        self._save()
        return len(docs)

    def query(self, question: str, k: int = 4) -> Tuple[str, List[Citation]]:
        if self.vectorstore is None:
            return "", []

        results = self.vectorstore.similarity_search_with_score(question, k=k)
        context_blocks: List[str] = []
        citations: List[Citation] = []
        for doc, score in results:
            preview = doc.page_content[:240].replace("\n", " ")
            context_blocks.append(doc.page_content)
            citations.append(
                Citation(
                    source=doc.metadata.get("source", "unknown"),
                    chunk_id=doc.metadata.get("chunk_id", "unknown"),
                    score=float(score),
                    preview=preview,
                )
            )
        return "\n\n---\n\n".join(context_blocks), citations

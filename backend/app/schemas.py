from typing import List, Optional

from pydantic import BaseModel


class Citation(BaseModel):
    source: str
    chunk_id: str
    score: float
    preview: str


class ChatRequest(BaseModel):
    session_id: str
    question: str
    k: int = 4


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]


class IngestURLRequest(BaseModel):
    url: str
    source_name: Optional[str] = None


class AdminStats(BaseModel):
    total_documents: int
    total_chunks: int
    sessions: int

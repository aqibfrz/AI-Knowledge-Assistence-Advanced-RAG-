from __future__ import annotations

import json
from typing import AsyncGenerator, List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_groq import ChatGroq

from .config import settings
from .ingestion import parse_docx, parse_pdf, parse_url
from .memory import ChatMemoryStore
from .rag import RAGStore
from .schemas import AdminStats, ChatRequest, ChatResponse, IngestURLRequest

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory = ChatMemoryStore()
rag_store = RAGStore()
llm = ChatGroq(
    model=settings.model_name,
    api_key=settings.groq_api_key or None,
    streaming=True,
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


@app.post("/ingest/files")
async def ingest_files(files: List[UploadFile] = File(...)) -> dict:
    ingested = []
    for file in files:
        raw = await file.read()
        name = file.filename or "unnamed"
        lower_name = name.lower()
        if lower_name.endswith(".pdf"):
            text = parse_pdf(raw)
        elif lower_name.endswith(".docx"):
            text = parse_docx(raw)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {name}")
        if not text.strip():
            raise HTTPException(status_code=400, detail=f"No extractable text found in: {name}")

        chunks = rag_store.add_text(text=text, source_name=name)
        ingested.append({"source": name, "chunks": chunks})
    return {"ingested": ingested}


@app.post("/ingest/url")
async def ingest_url(payload: IngestURLRequest) -> dict:
    text = await parse_url(payload.url)
    source = payload.source_name or payload.url
    chunks = rag_store.add_text(text=text, source_name=source)
    return {"source": source, "chunks": chunks}


def _compose_prompt(history: str, context: str, question: str) -> str:
    return (
        "You are an enterprise knowledge assistant. Use ONLY supplied context.\n"
        "If information is missing, clearly say you do not know.\n\n"
        f"Conversation history:\n{history or '(none)'}\n\n"
        f"Retrieved context:\n{context or '(none)'}\n\n"
        f"Question: {question}\n\n"
        "Answer in concise paragraphs."
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    context, citations = rag_store.query(payload.question, payload.k)
    history = memory.get_context(payload.session_id)
    prompt = _compose_prompt(history, context, payload.question)
    result = await llm.ainvoke(prompt)
    answer = result.content if isinstance(result.content, str) else str(result.content)
    memory.add_turn(payload.session_id, payload.question, answer)
    return ChatResponse(answer=answer, citations=citations)


@app.post("/chat/stream")
async def chat_stream(payload: ChatRequest) -> StreamingResponse:
    context, citations = rag_store.query(payload.question, payload.k)
    history = memory.get_context(payload.session_id)
    prompt = _compose_prompt(history, context, payload.question)

    async def token_stream() -> AsyncGenerator[str, None]:
        answer_fragments: List[str] = []
        yield "event: citations\ndata: " + json.dumps([c.model_dump() for c in citations]) + "\n\n"
        async for chunk in llm.astream(prompt):
            token = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
            if token:
                answer_fragments.append(token)
                clean_token = token.replace("\n", "\\n")
                yield f"event: token\ndata: {clean_token}\n\n"
        final_answer = "".join(answer_fragments)
        memory.add_turn(payload.session_id, payload.question, final_answer)
        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(token_stream(), media_type="text/event-stream")


@app.get("/admin/stats", response_model=AdminStats)
async def admin_stats() -> AdminStats:
    return AdminStats(
        total_documents=rag_store.total_documents,
        total_chunks=rag_store.total_chunks,
        sessions=memory.session_count(),
    )

import os
from pathlib import Path
from urllib.parse import urlparse
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from app.rag.store import get_vector_store
from app.rag.loader import load_pdf, load_website

load_dotenv()

router = APIRouter(prefix="/rag", tags=["RAG"])

UPLOAD_DIR = Path("uploads").resolve()
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))  # 20 MB default

_ALLOWED_URL_SCHEMES = {"http", "https"}
_BLOCKED_HOSTS = {"169.254.169.254", "metadata.google.internal", "localhost", "127.0.0.1", "::1"}

_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)

_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a helpful assistant. Answer the question using only the provided context. "
        "If the answer is not in the context, say you don't know.\n\nContext:\n{context}",
    ),
    ("human", "{input}"),
])


def _extract_sources(context: list) -> list[dict]:
    seen: set[str] = set()
    sources = []
    for doc in context:
        src = doc.metadata.get("source", "")
        if not src or src in seen:
            continue
        seen.add(src)
        if src.startswith("http://") or src.startswith("https://"):
            sources.append({"type": "url", "label": src, "href": src})
        else:
            filename = Path(src).name
            sources.append({"type": "file", "label": filename, "href": f"/rag/download/{filename}"})
    return sources


def _ingest_pdf(file_path: str) -> int:
    docs = load_pdf(file_path)
    get_vector_store().add_documents(docs)
    return len(docs)


def _ingest_url(url: str) -> int:
    docs = load_website(url)
    get_vector_store().add_documents(docs)
    return len(docs)


def _query_rag(question: str) -> dict:
    store = get_vector_store()
    retriever = store.as_retriever(search_kwargs={"k": 4})
    chain = create_retrieval_chain(
        retriever,
        create_stuff_documents_chain(_llm, _prompt),
    )
    result = chain.invoke({"input": question})
    return {
        "answer": result["answer"],
        "sources": _extract_sources(result["context"]),
    }


class ScrapeRequest(BaseModel):
    url: str


class QueryRequest(BaseModel):
    question: str


def _safe_filename(filename: str) -> str:
    name = Path(filename).name
    if not name or name != filename or "/" in name or "\\" in name:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return name


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_URL_SCHEMES:
        raise HTTPException(status_code=400, detail="Only http/https URLs are allowed")
    host = parsed.hostname or ""
    if host in _BLOCKED_HOSTS:
        raise HTTPException(status_code=400, detail="URL host is not allowed")


@router.post("/upload-pdf", summary="Upload a PDF and store in Qdrant")
async def upload_pdf(file: UploadFile = File(...)):
    if not (file.filename or "").endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    safe_name = _safe_filename(file.filename)
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_UPLOAD_BYTES // (1024*1024)} MB limit")

    save_path = UPLOAD_DIR / safe_name
    save_path.write_bytes(content)

    try:
        chunk_count = await run_in_threadpool(_ingest_pdf, str(save_path))
        return {
            "message": f"Stored {chunk_count} chunks from '{safe_name}'",
            "saved_path": str(save_path),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape", summary="Scrape a website and store in Qdrant")
async def scrape_website(request: ScrapeRequest):
    _validate_url(request.url)
    try:
        chunk_count = await run_in_threadpool(_ingest_url, request.url)
        return {"message": f"Stored {chunk_count} chunks from {request.url}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/query", summary="Query the RAG knowledge base")
async def query_rag(request: QueryRequest):
    try:
        result = await run_in_threadpool(_query_rag, request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filename}", summary="Download an uploaded PDF")
def download_file(filename: str):
    safe_name = _safe_filename(filename)
    file_path = (UPLOAD_DIR / safe_name).resolve()
    if not str(file_path).startswith(str(UPLOAD_DIR)):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=str(file_path), filename=safe_name, media_type="application/pdf")

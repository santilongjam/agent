import os
from pathlib import Path
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

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

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


@router.post("/upload-pdf", summary="Upload a PDF and store in Qdrant")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    save_path = UPLOAD_DIR / file.filename
    save_path.write_bytes(await file.read())

    try:
        chunk_count = await run_in_threadpool(_ingest_pdf, str(save_path))
        return {
            "message": f"Stored {chunk_count} chunks from '{file.filename}'",
            "saved_path": str(save_path),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape", summary="Scrape a website and store in Qdrant")
async def scrape_website(request: ScrapeRequest):
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
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=str(file_path), filename=filename, media_type="application/pdf")

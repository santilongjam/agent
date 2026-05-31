import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers import tasks, users, agent, rag
from app.database import init_db

load_dotenv()

_REQUIRED_ENV_VARS = ["GROQ_API_KEY", "QDRANT_URL", "QDRANT_API_KEY"]

def _validate_env():
    missing = [v for v in _REQUIRED_ENV_VARS if not os.getenv(v)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

_validate_env()

_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()] or ["*"]

app = FastAPI(
    title="Tasks API",
    description="A simple CRUD API for managing tasks.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.include_router(tasks.router)
app.include_router(users.router)
app.include_router(agent.router)
app.include_router(rag.router)


@app.get("/", tags=["Health"], summary="Health check")
def index():
    return {"status": "ok", "data": "Hello Yohan!"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import tasks, users
from app.database import init_db

app = FastAPI(
    title="Tasks API",
    description="A simple CRUD API for managing tasks.",
    version="1.0.0",
)

# For CORS - used for security - domain restriction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.include_router(tasks.router)
app.include_router(users.router)

# Try to include agent router, but don't fail if it has issues
try:
    from app.routers import agent
    app.include_router(agent.router)
except Exception as e:
    print(f"Warning: Could not load agent router: {e}")

# Try to include RAG router, but don't fail if it has issues
try:
    from app.routers import rag
    app.include_router(rag.router)
except Exception as e:
    print(f"Warning: Could not load RAG router: {e}")


@app.get("/", tags=["Health"], summary="Health check")
def index():
    return {"status": "ok", "data": "Hello Yohan!"}


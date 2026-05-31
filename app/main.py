from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import tasks, users, agent, rag
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
app.include_router(agent.router)
app.include_router(rag.router)


@app.get("/", tags=["Health"], summary="Health check")
def index():
    return {"status": "ok", "data": "Hello Yohan!"}

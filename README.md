# test1-app

A FastAPI application with LangGraph agents, RAG (Retrieval-Augmented Generation), and task/user management APIs backed by MySQL and Qdrant.

## Prerequisites

- [Python 3.12+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — fast Python package manager
- MySQL running locally (or accessible remotely)
- [Qdrant](https://qdrant.tech/) instance (local or cloud)

## Setup

### 1. Clone and install dependencies

```bash
uv sync
```

### 2. Configure environment variables

Copy the example below into a `.env` file at the project root and fill in your values:

```env
# MySQL
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=agent_db

# Qdrant (local or cloud URL)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_api_key

# LLM — Groq API key
GROQ_API_KEY=your_groq_api_key

# User agent string
USER_AGENT=test1-app/1.0

# Hugging Face token (optional)
HF_TOKEN=your_hf_token
```

### 3. Create the MySQL database

```sql
CREATE DATABASE agent_db;
```

The app creates all tables automatically on startup via `init_db()`.

## Running the App

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

Interactive docs: `http://localhost:8000/docs`

## Project Structure

```
app/
├── main.py          # FastAPI app entry point
├── database.py      # DB connection and init
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic schemas
├── routers/         # API routes (tasks, users, agent, rag)
├── agents/          # LangGraph agent, tools, memory
└── rag/             # RAG loader and vector store
```

## API Routes

| Prefix    | Description                        |
|-----------|------------------------------------|
| `/`       | Health check                       |
| `/tasks`  | Task CRUD                          |
| `/users`  | User CRUD                          |
| `/agent`  | LangGraph agent chat               |
| `/rag`    | Document ingestion and RAG queries |

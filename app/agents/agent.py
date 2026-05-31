import os
import sqlite3
from typing import Generator
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk

from app.agents.tools import get_all_tasks, get_task, create_task, update_task, delete_task

load_dotenv()

_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)

_tools = [get_all_tasks, get_task, create_task, update_task, delete_task]

_system_prompt = (
    "You are a helpful task management assistant. "
    "You can list, create, update, and delete tasks in the database. "
    "Always confirm actions with the user's intent and be concise in your responses."
)

_database_url = os.getenv("DATABASE_URL", "")

if _database_url:
    from langgraph.checkpoint.postgres import PostgresSaver
    _memory = PostgresSaver.from_conn_string(_database_url)
    _memory.setup()
else:
    from langgraph.checkpoint.sqlite import SqliteSaver
    _checkpoints_db = os.getenv("CHECKPOINTS_DB_PATH", "checkpoints.db")
    _conn = sqlite3.connect(_checkpoints_db, check_same_thread=False)
    _memory = SqliteSaver(_conn)

agent = create_agent(_llm, _tools, checkpointer=_memory, system_prompt=_system_prompt)


# below tow methods are same only diffrence is - response of last once is in streaming

def run_agent(message: str, thread_id: str = "default") -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        config=config,
    )
    messages = result["messages"]
    return {
        "response": messages[-1].content,
        "message_count": len(messages),
    }


def stream_agent(message: str, thread_id: str = "default") -> Generator[str, None, None]:
    config = {"configurable": {"thread_id": thread_id}}
    for chunk, _ in agent.stream(
        {"messages": [{"role": "user", "content": message}]},
        config=config,
        stream_mode="messages",
    ):
        if isinstance(chunk, AIMessageChunk) and chunk.content:
            yield chunk.content

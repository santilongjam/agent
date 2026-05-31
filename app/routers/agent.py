import json
import uuid
from typing import Optional, Generator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents.agent import agent, run_agent, stream_agent

router = APIRouter(prefix="/agent", tags=["Agent"])


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    message_count: int


@router.post("/chat", response_model=ChatResponse, summary="Chat with the task management agent")
def chat(request: ChatRequest):
    try:
        thread_id = request.thread_id or str(uuid.uuid4())
        result = run_agent(request.message, thread_id=thread_id)
        return ChatResponse(
            response=result["response"],
            thread_id=thread_id,
            message_count=result["message_count"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream", summary="Stream chat with the task management agent (SSE)")
def chat_stream(request: ChatRequest):
    thread_id = request.thread_id or str(uuid.uuid4())

    def generate() -> Generator[str, None, None]:
        try:
            for token in stream_agent(request.message, thread_id=thread_id):
                yield f"data: {json.dumps({'token': token})}\n\n"

            config = {"configurable": {"thread_id": thread_id}}
            state = agent.get_state(config)
            message_count = len(state.values.get("messages", []))
            yield f"data: {json.dumps({'done': True, 'thread_id': thread_id, 'message_count': message_count})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )

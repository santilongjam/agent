from app.database import SessionLocal
from app.models.conversation import ConversationMessage


def load_history(thread_id: str) -> list[dict]:
    db = SessionLocal()
    try:
        rows = (
            db.query(ConversationMessage)
            .filter(ConversationMessage.thread_id == thread_id)
            .order_by(ConversationMessage.id)
            .all()
        )
        return [{"role": r.role, "content": r.content} for r in rows]
    finally:
        db.close()


def save_messages(thread_id: str, messages: list[dict]) -> None:
    db = SessionLocal()
    try:
        for msg in messages:
            db.add(ConversationMessage(
                thread_id=thread_id,
                role=msg["role"],
                content=msg["content"],
            ))
        db.commit()
    finally:
        db.close()


def count_messages(thread_id: str) -> int:
    db = SessionLocal()
    try:
        return (
            db.query(ConversationMessage)
            .filter(ConversationMessage.thread_id == thread_id)
            .count()
        )
    finally:
        db.close()

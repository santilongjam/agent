from typing import Optional
from langchain_core.tools import tool
from app.database import SessionLocal
from app.models.task import TaskModel


def _session():
    return SessionLocal()


@tool
def get_all_tasks() -> list[dict]:
    """Get all tasks from the database. Returns a list of all tasks with their id, title, description, and completed status."""
    db = _session()
    try:
        tasks = db.query(TaskModel).all()
        return [
            {"id": t.id, "title": t.title, "description": t.description, "completed": t.completed}
            for t in tasks
        ]
    finally:
        db.close()


@tool
def get_task(task_id: int) -> dict:
    """Get a single task by its ID. Returns the task details or an error message if not found."""
    db = _session()
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not task:
            return {"error": f"Task {task_id} not found"}
        return {"id": task.id, "title": task.title, "description": task.description, "completed": task.completed}
    finally:
        db.close()


@tool
def create_task(title: str, description: Optional[str] = None, completed: bool = False) -> dict:
    """Create a new task with a title, optional description, and optional completed status (defaults to False)."""
    db = _session()
    try:
        task = TaskModel(title=title, description=description, completed=completed)
        db.add(task)
        db.commit()
        db.refresh(task)
        return {"id": task.id, "title": task.title, "description": task.description, "completed": task.completed}
    finally:
        db.close()


@tool
def update_task(task_id: int, title: Optional[str] = None, description: Optional[str] = None, completed: Optional[bool] = None) -> dict:
    """Update an existing task by ID. Only provided fields are updated. Returns the updated task or an error if not found."""
    db = _session()
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not task:
            return {"error": f"Task {task_id} not found"}
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if completed is not None:
            task.completed = completed
        db.commit()
        db.refresh(task)
        return {"id": task.id, "title": task.title, "description": task.description, "completed": task.completed}
    finally:
        db.close()


@tool
def delete_task(task_id: int) -> dict:
    """Delete a task by its ID. Returns a confirmation message or an error if not found."""
    db = _session()
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not task:
            return {"error": f"Task {task_id} not found"}
        db.delete(task)
        db.commit()
        return {"message": f"Task {task_id} deleted successfully"}
    finally:
        db.close()

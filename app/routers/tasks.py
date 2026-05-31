from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.schemas.task import TaskCreate, TaskUpdate, TaskOut
from app.models.task import TaskModel
from app.database import get_db

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ── READ ALL ──────────────────────────────────────────────────────────────────
@router.get("/list", response_model=List[TaskOut], summary="Get all tasks")
def get_all_tasks(db: Session = Depends(get_db)):
    return db.query(TaskModel).all()


# ── READ ONE ──────────────────────────────────────────────────────────────────
@router.get("/data/{task_id}", response_model=TaskOut, summary="Get a task by ID")
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ── CREATE ────────────────────────────────────────────────────────────────────
@router.post("/create", response_model=TaskOut, status_code=201, summary="Create a task")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    new_task = TaskModel(
        title=task.title,
        description=task.description,
        completed=task.completed,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


# ── UPDATE ────────────────────────────────────────────────────────────────────
@router.put("/update/{task_id}", response_model=TaskOut, summary="Update a task")
def update_task(task_id: int, updates: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


# ── DELETE ────────────────────────────────────────────────────────────────────
@router.delete("/delete/{task_id}", summary="Delete a task")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"message": f"Task {task_id} deleted"}

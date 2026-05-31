from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import UserModel
from app.schemas.user import UserCreate, UserUpdate, UserOut

router = APIRouter(prefix="/users", tags=["Users"])


# ── READ ALL ──────────────────────────────────────────────────────────────────
@router.get("/list", response_model=List[UserOut], summary="Get all users")
def get_all_users(db: Session = Depends(get_db)):
    return db.query(UserModel).all()


# ── READ ONE ──────────────────────────────────────────────────────────────────
@router.get("/data/{user_id}", response_model=UserOut, summary="Get a user by ID")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ── CREATE ────────────────────────────────────────────────────────────────────
@router.post("/create", response_model=UserOut, status_code=201, summary="Create a user")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = UserModel(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# ── UPDATE ────────────────────────────────────────────────────────────────────
@router.put("/update/{user_id}", response_model=UserOut, summary="Update a user")
def update_user(user_id: int, updates: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


# ── DELETE ────────────────────────────────────────────────────────────────────
@router.delete("/delete/{user_id}", summary="Delete a user")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": f"User {user_id} deleted"}

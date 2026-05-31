from fastapi import APIRouter, HTTPException
from typing import List

from app.schemas.user import UserCreate, UserUpdate, UserOut

router = APIRouter(prefix="/users", tags=["Users"])

db: dict[int, dict] = {}
next_id = 1


# ── READ ALL ──────────────────────────────────────────────────────────────────
@router.get("/list", response_model=List[UserOut], summary="Get all users")
def get_all_users():
    return list(db.values())


# ── READ ONE ──────────────────────────────────────────────────────────────────
@router.get("/data/{user_id}", response_model=UserOut, summary="Get a user by ID")
def get_user(user_id: int):
    if user_id not in db:
        raise HTTPException(status_code=404, detail="User not found")
    return db[user_id]


# ── CREATE ────────────────────────────────────────────────────────────────────
@router.post("/create", response_model=UserOut, status_code=201, summary="Create a user")
def create_user(user: UserCreate):
    global next_id

    new_user = {
        "id": next_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
    }

    db[next_id] = new_user
    next_id += 1

    return new_user


# ── UPDATE ────────────────────────────────────────────────────────────────────
@router.put("/update/{user_id}", response_model=UserOut, summary="Update a user")
def update_user(user_id: int, updates: UserUpdate):
    if user_id not in db:
        raise HTTPException(status_code=404, detail="User not found")

    user = db[user_id]

    for field, value in updates.model_dump(exclude_unset=True).items():
        user[field] = value

    return user


# ── DELETE ────────────────────────────────────────────────────────────────────
@router.delete("/delete/{user_id}", summary="Delete a user")
def delete_user(user_id: int):
    if user_id not in db:
        raise HTTPException(status_code=404, detail="User not found")

    del db[user_id]
    return {"message": f"User {user_id} deleted"}

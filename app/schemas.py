from pydantic import BaseModel
from typing import Optional


# This is the shape of data the user sends when CREATING a task
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None  # optional — can be left blank
    completed: bool = False             # defaults to False (not done yet)


# This is the shape of data the user sends when UPDATING a task
# Every field is Optional so you can update just one field at a time
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None


# This is the shape of data we SEND BACK to the user
# It includes the auto-generated id
class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    completed: bool


# ── User Schemas ───────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool

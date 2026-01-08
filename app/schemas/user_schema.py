from pydantic import BaseModel, Field
from typing import Optional

class UserBase(BaseModel):
    username: str
    rol: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)
    rol: Optional[str] = None

class UserOut(UserBase):
    id: int

    class Config:
        from_attributes = True

from pydantic import BaseModel

class LoginSchema(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserAuthOut(BaseModel):
    id: int
    username: str
    rol: str

    class Config:
        from_attributes = True

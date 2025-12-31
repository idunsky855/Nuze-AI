from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    name: Optional[str] = None

class UserLogin(UserBase):
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: UUID

class UserResponse(UserBase):
    id: UUID
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    is_onboarded: bool = False

    class Config:
        from_attributes = True

class UserOnboarding(BaseModel):
    age: int
    gender: str
    location: str
    preferences: list[str]

class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class UserRegister(BaseModel):
    account: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    phone: Optional[str] = None
    email: Optional[str] = None

    @model_validator(mode="after")
    def require_contact(self):
        if not self.phone and not self.email:
            raise ValueError("请提供手机号或邮箱")
        return self


class UserLogin(BaseModel):
    account: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    account: str
    phone: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    avatar_url: Optional[str] = None


class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

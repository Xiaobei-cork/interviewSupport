from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ShareCardOut(BaseModel):
    id: int
    user_id: int
    username: str
    avatar_url: Optional[str] = None
    company_name: str
    job_title: str
    score: Optional[float] = None
    interview_time: datetime
    like_count: int = 0
    comment_count: int = 0
    favorite_count: int = 0
    view_count: int = 0
    is_liked: bool = False
    is_favorited: bool = False
    ai_summary: Optional[str] = None
    tags: list[str] = []


class CommentOut(BaseModel):
    id: int
    user_id: int
    username: str
    avatar_url: Optional[str] = None
    content: str
    parent_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None

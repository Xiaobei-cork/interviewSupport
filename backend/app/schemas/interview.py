from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class InterviewCreate(BaseModel):
    company_name: str = Field(..., max_length=100)
    job_title: str = Field(..., max_length=100)
    job_jd: Optional[str] = None
    remark: Optional[str] = None
    interview_time: datetime
    visibility: int = 1
    public_audio: int = 0


class InterviewUpdate(BaseModel):
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    job_jd: Optional[str] = None
    remark: Optional[str] = None
    interview_time: Optional[datetime] = None
    visibility: Optional[int] = None
    public_audio: Optional[int] = None
    audio_url: Optional[str] = None


class InterviewOut(BaseModel):
    id: int
    user_id: int
    company_name: str
    job_title: str
    job_jd: Optional[str] = None
    remark: Optional[str] = None
    audio_url: Optional[str] = None
    interview_time: datetime
    ai_analysis: Optional[str] = None
    score: Optional[float] = None
    ai_adopted: bool = False
    visibility: int
    public_audio: int
    created_at: datetime
    updated_at: datetime
    like_count: int = 0
    comment_count: int = 0
    favorite_count: int = 0
    is_liked: bool = False
    is_favorited: bool = False

    class Config:
        from_attributes = True


class ScoreUpdate(BaseModel):
    score: float = Field(..., ge=0, le=5)


class AiAdoptRequest(BaseModel):
    score: Optional[float] = Field(None, ge=0, le=5)


class AiChatRequest(BaseModel):
    message: str

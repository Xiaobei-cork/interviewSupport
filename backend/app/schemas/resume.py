from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ResumeOut(BaseModel):
    id: int
    user_id: int
    file_name: str
    file_url: str
    file_type: str
    ai_analysis: Optional[str] = None
    score: Optional[float] = None
    ai_adopted: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResumeAiAdoptRequest(BaseModel):
    score: Optional[float] = Field(None, ge=0, le=5)


class ResumeDeepOptimizeRequest(BaseModel):
    requirement: str = Field(..., min_length=1, max_length=2000)


class ResumeExperienceItem(BaseModel):
    period: str = ""
    company: str = ""
    title: str = ""
    current: bool = False
    bullets: list[str] = []


class ResumeOptimizedPreview(BaseModel):
    name: str = ""
    phone: str = ""
    email: str = ""
    location: str = ""
    summary: str = ""
    experiences: list[ResumeExperienceItem] = []


class ResumeSaveOptimizedRequest(BaseModel):
    preview: ResumeOptimizedPreview

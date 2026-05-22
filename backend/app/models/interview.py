from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, Float, SmallInteger, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class InterviewRecord(Base):
    __tablename__ = "interview_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(100), nullable=False)
    job_title: Mapped[str] = mapped_column(String(100), nullable=False)
    job_jd: Mapped[str | None] = mapped_column(Text, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    interview_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ai_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_adopted: Mapped[int] = mapped_column(SmallInteger, default=0)  # 1=用户已采纳当前 AI 分析
    visibility: Mapped[int] = mapped_column(SmallInteger, default=1)  # 0=私密 1=公开 2=仅好友
    public_audio: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="interviews")
    likes = relationship("InterviewLike", back_populates="interview", cascade="all, delete-orphan")
    favorites = relationship("InterviewFavorite", back_populates="interview", cascade="all, delete-orphan")
    comments = relationship("InterviewComment", back_populates="interview", cascade="all, delete-orphan")


class InterviewLike(Base):
    __tablename__ = "interview_like"
    __table_args__ = (UniqueConstraint("user_id", "interview_id", name="uq_like"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    interview_id: Mapped[int] = mapped_column(Integer, ForeignKey("interview_record.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    interview = relationship("InterviewRecord", back_populates="likes")


class InterviewFavorite(Base):
    __tablename__ = "interview_favorite"
    __table_args__ = (UniqueConstraint("user_id", "interview_id", name="uq_favorite"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    interview_id: Mapped[int] = mapped_column(Integer, ForeignKey("interview_record.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    interview = relationship("InterviewRecord", back_populates="favorites")


class InterviewComment(Base):
    __tablename__ = "interview_comment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    interview_id: Mapped[int] = mapped_column(Integer, ForeignKey("interview_record.id"), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("interview_comment.id"), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)  # 1=正常 0=删除 2=举报
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    interview = relationship("InterviewRecord", back_populates="comments")
    user = relationship("User")

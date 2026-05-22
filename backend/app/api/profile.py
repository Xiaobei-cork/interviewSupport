from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.api.deps import get_current_user_optional
from app.models.user import User
from app.models.interview import InterviewRecord, InterviewLike, InterviewFavorite
from app.models.social import UserFriend
from app.core.response import ok, api_raise
from app.services.storage import enrich_media_url

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/{user_id}")
def get_profile(
    user_id: int,
    viewer=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        api_raise(404, "用户不存在")

    interviews = (
        db.query(InterviewRecord)
        .filter(InterviewRecord.user_id == user_id, InterviewRecord.visibility == 1)
        .order_by(InterviewRecord.created_at.desc())
        .limit(20)
        .all()
    )

    favorites = []
    if viewer:
        favs = (
            db.query(InterviewFavorite)
            .filter(InterviewFavorite.user_id == viewer.id)
            .limit(20)
            .all()
        )
        favorites = [f.interview_id for f in favs]

    like_count = db.query(func.count(InterviewLike.id)).join(InterviewRecord).filter(
        InterviewRecord.user_id == user_id
    ).scalar() or 0

    friend_count = db.query(UserFriend).filter(
        ((UserFriend.user_id == user_id) | (UserFriend.friend_id == user_id)),
        UserFriend.status == "accepted",
    ).count()

    return ok(
        data={
            "user": {
                "id": user.id,
                "username": user.username,
                "avatar_url": enrich_media_url(user.avatar_url),
                "created_at": user.created_at.isoformat(),
            },
            "stats": {
                "interview_count": len(interviews),
                "like_count": like_count,
                "friend_count": friend_count,
            },
            "interviews": [
                {
                    "id": i.id,
                    "company_name": i.company_name,
                    "job_title": i.job_title,
                    "score": i.score,
                    "interview_time": i.interview_time.isoformat(),
                }
                for i in interviews
            ],
            "favorite_ids": favorites,
        },
        message="获取成功",
    )

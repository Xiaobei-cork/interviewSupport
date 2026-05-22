import json
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.api.deps import get_current_user, get_current_user_optional
from app.models.user import User
from app.models.interview import InterviewRecord, InterviewLike, InterviewFavorite, InterviewComment
from app.models.social import UserFriend
from app.schemas.share import CommentCreate
from app.core.response import ok, api_raise
from app.api.interviews import _to_dict
from app.services.storage import enrich_media_url
from app.utils.redis_client import cache_get, cache_set, cache_delete

router = APIRouter(prefix="/share", tags=["share"])


def _can_view(record: InterviewRecord, viewer: Optional[User], db: Session) -> bool:
    if record.visibility == 1:
        return True
    if not viewer:
        return False
    if record.user_id == viewer.id:
        return True
    if record.visibility == 0:
        return False
    if record.visibility == 2:
        friendship = (
            db.query(UserFriend)
            .filter(
                UserFriend.status == "accepted",
                ((UserFriend.user_id == viewer.id) & (UserFriend.friend_id == record.user_id))
                | ((UserFriend.user_id == record.user_id) & (UserFriend.friend_id == viewer.id)),
            )
            .first()
        )
        return friendship is not None
    return False


@router.get("/feed")
def share_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    viewer: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    cache_key = f"share:feed:{page}:{page_size}"
    cached = cache_get(cache_key)
    if cached and not viewer:
        return ok(data=cached, message="查询成功")

    q = (
        db.query(InterviewRecord)
        .options(joinedload(InterviewRecord.user), joinedload(InterviewRecord.likes), joinedload(InterviewRecord.comments))
        .filter(InterviewRecord.visibility == 1)
        .order_by(InterviewRecord.created_at.desc())
    )
    total = q.count()
    records = q.offset((page - 1) * page_size).limit(page_size).all()
    items = []
    for r in records:
        if not _can_view(r, viewer, db):
            continue
        ai_summary = None
        if r.ai_analysis:
            try:
                data = json.loads(r.ai_analysis)
                ai_summary = data.get("overall", "")[:100]
            except Exception:
                ai_summary = r.ai_analysis[:100]
        is_liked = viewer and any(l.user_id == viewer.id for l in r.likes)
        is_fav = viewer and any(f.user_id == viewer.id for f in r.favorites)
        items.append({
            "id": r.id,
            "user_id": r.user_id,
            "username": r.user.username if r.user else "",
            "avatar_url": enrich_media_url(r.user.avatar_url if r.user else None),
            "company_name": r.company_name,
            "job_title": r.job_title,
            "score": r.score,
            "interview_time": r.interview_time.isoformat() if r.interview_time else None,
            "like_count": len(r.likes),
            "comment_count": len([c for c in r.comments if c.status == 1]),
            "favorite_count": len(r.favorites),
            "is_liked": bool(is_liked),
            "is_favorited": bool(is_fav),
            "ai_summary": ai_summary,
            "tags": ["社招"] if r.visibility == 1 else [],
        })
    payload = {"items": items, "total": total, "page": page, "page_size": page_size}
    if not viewer:
        cache_set(cache_key, payload, ttl=300)
    return ok(data=payload, message="查询成功")


@router.get("/{record_id}")
def share_detail(
    record_id: int,
    viewer: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    record = (
        db.query(InterviewRecord)
        .options(joinedload(InterviewRecord.likes), joinedload(InterviewRecord.favorites), joinedload(InterviewRecord.comments))
        .filter(InterviewRecord.id == record_id)
        .first()
    )
    if not record or not _can_view(record, viewer, db):
        api_raise(404, "记录不存在或无权访问")
    return ok(data=_to_dict(record, viewer), message="获取成功")


@router.post("/{record_id}/like")
def toggle_like(
    record_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(InterviewRecord).filter(InterviewRecord.id == record_id).first()
    if not record:
        api_raise(404, "记录不存在")
    existing = (
        db.query(InterviewLike)
        .filter(InterviewLike.user_id == user.id, InterviewLike.interview_id == record_id)
        .first()
    )
    if existing:
        db.delete(existing)
        liked = False
    else:
        db.add(InterviewLike(user_id=user.id, interview_id=record_id))
        liked = True
    db.commit()
    cache_delete("share:feed:1:10")
    return ok(
        data={
            "liked": liked,
            "like_count": db.query(InterviewLike).filter(InterviewLike.interview_id == record_id).count(),
        },
        message="操作成功",
    )


@router.post("/{record_id}/favorite")
def toggle_favorite(
    record_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(InterviewRecord).filter(InterviewRecord.id == record_id).first()
    if not record:
        api_raise(404, "记录不存在")
    existing = (
        db.query(InterviewFavorite)
        .filter(InterviewFavorite.user_id == user.id, InterviewFavorite.interview_id == record_id)
        .first()
    )
    if existing:
        db.delete(existing)
        favorited = False
    else:
        db.add(InterviewFavorite(user_id=user.id, interview_id=record_id))
        favorited = True
    db.commit()
    return ok(data={"favorited": favorited}, message="操作成功")


@router.get("/{record_id}/comments")
def list_comments(
    record_id: int,
    limit: int = Query(3, ge=1, le=50),
    db: Session = Depends(get_db),
):
    total = db.query(InterviewComment).filter(
        InterviewComment.interview_id == record_id, InterviewComment.status == 1
    ).count()
    comments = (
        db.query(InterviewComment)
        .options(joinedload(InterviewComment.user))
        .filter(InterviewComment.interview_id == record_id, InterviewComment.status == 1)
        .order_by(InterviewComment.created_at.desc())
        .limit(limit)
        .all()
    )
    items = [
        {
            "id": c.id,
            "user_id": c.user_id,
            "username": c.user.username if c.user else "",
            "avatar_url": enrich_media_url(c.user.avatar_url if c.user else None),
            "content": c.content,
            "parent_id": c.parent_id,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in comments
    ]
    return ok(data={"items": items, "total": total}, message="查询成功")


@router.post("/{record_id}/comments")
def create_comment(
    record_id: int,
    data: CommentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(InterviewRecord).filter(InterviewRecord.id == record_id).first()
    if not record:
        api_raise(404, "记录不存在")
    comment = InterviewComment(
        user_id=user.id,
        interview_id=record_id,
        content=data.content,
        parent_id=data.parent_id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    cache_delete(f"share:comments:{record_id}")
    return ok(
        data={
            "id": comment.id,
            "user_id": user.id,
            "username": user.username,
            "avatar_url": enrich_media_url(user.avatar_url),
            "content": comment.content,
            "parent_id": comment.parent_id,
            "created_at": comment.created_at.isoformat() if comment.created_at else None,
        },
        message="评论成功",
    )


@router.put("/comments/{comment_id}")
def update_comment(
    comment_id: int,
    data: CommentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.query(InterviewComment).filter(InterviewComment.id == comment_id, InterviewComment.user_id == user.id).first()
    if not c:
        api_raise(404, "评论不存在")
    c.content = data.content
    db.commit()
    db.refresh(c)
    return ok(
        data={
            "id": c.id,
            "user_id": c.user_id,
            "username": user.username,
            "avatar_url": enrich_media_url(user.avatar_url),
            "content": c.content,
            "parent_id": c.parent_id,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        },
        message="更新成功",
    )


@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.query(InterviewComment).filter(InterviewComment.id == comment_id, InterviewComment.user_id == user.id).first()
    if not c:
        api_raise(404, "评论不存在")
    c.status = 0
    db.commit()
    return ok(message="删除成功")


@router.post("/comments/{comment_id}/report")
def report_comment(comment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.query(InterviewComment).filter(InterviewComment.id == comment_id).first()
    if not c:
        api_raise(404, "评论不存在")
    c.status = 2
    db.commit()
    return ok(message="举报已提交")

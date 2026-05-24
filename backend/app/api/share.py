import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from app.database import get_db
from app.api.deps import get_current_user, get_current_user_optional
from app.db.interview_helpers import interview_to_dict, load_feed_relations
from app.models.user import User
from app.models.interview import (
    InterviewRecord,
    InterviewLike,
    InterviewFavorite,
    InterviewComment,
)
from app.models.social import UserFriend
from app.schemas.share import CommentCreate
from app.core.response import ok, api_raise
from app.services.storage import enrich_media_url
from app.services.message_service import notify_interview_comment, notify_interview_like
from app.utils.redis_client import cache_get, cache_set, cache_delete

router = APIRouter(prefix="/share", tags=["share"])


async def _can_view(record: InterviewRecord, viewer: Optional[User]) -> bool:
    if record.visibility == 1:
        return True
    if not viewer:
        return False
    if record.user_id == viewer.id:
        return True
    if record.visibility == 0:
        return False
    if record.visibility == 2:
        friendship = await UserFriend.aio_get_or_none(
            (UserFriend.status == "accepted")
            & (
                ((UserFriend.user == viewer.id) & (UserFriend.friend == record.user_id))
                | ((UserFriend.user == record.user_id) & (UserFriend.friend == viewer.id))
            )
        )
        return friendship is not None
    return False


@router.get("/feed")
async def share_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    viewer: Optional[User] = Depends(get_current_user_optional),
    _db=Depends(get_db),
):
    cache_key = f"share:feed:{page}:{page_size}"
    cached = cache_get(cache_key)
    if cached and not viewer:
        return ok(data=cached, message="查询成功")

    q = (
        InterviewRecord.select()
        .where(InterviewRecord.visibility == 1)
        .order_by(InterviewRecord.created_at.desc())
    )
    total = await q.aio_count()
    records = list(await q.paginate(page, page_size).aio_execute())
    likes_map, comments_map, favorites_map, users_map = await load_feed_relations(records)

    items = []
    for r in records:
        if not await _can_view(r, viewer):
            continue
        ai_summary = None
        if r.ai_analysis:
            try:
                data = json.loads(r.ai_analysis)
                ai_summary = data.get("overall", "")[:100]
            except Exception:
                ai_summary = r.ai_analysis[:100]
        likes = likes_map.get(r.id, [])
        comments = comments_map.get(r.id, [])
        favorites = favorites_map.get(r.id, [])
        owner = users_map.get(r.user_id)
        is_liked = viewer and any(l.user_id == viewer.id for l in likes)
        is_fav = viewer and any(f.user_id == viewer.id for f in favorites)
        items.append({
            "id": r.id,
            "user_id": r.user_id,
            "username": owner.username if owner else "",
            "avatar_url": enrich_media_url(owner.avatar_url if owner else None),
            "company_name": r.company_name,
            "job_title": r.job_title,
            "score": r.score,
            "interview_time": r.interview_time.isoformat() if r.interview_time else None,
            "like_count": len(likes),
            "comment_count": len(comments),
            "favorite_count": len(favorites),
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
async def share_detail(
    record_id: int,
    viewer: Optional[User] = Depends(get_current_user_optional),
    _db=Depends(get_db),
):
    record = await InterviewRecord.aio_get_or_none(InterviewRecord.id == record_id)
    if not record or not await _can_view(record, viewer):
        api_raise(404, "记录不存在或无权访问")
    return ok(data=await interview_to_dict(record, viewer), message="获取成功")


@router.post("/{record_id}/like")
async def toggle_like(
    record_id: int,
    user: User = Depends(get_current_user),
    _db=Depends(get_db),
):
    record = await InterviewRecord.aio_get_or_none(InterviewRecord.id == record_id)
    if not record:
        api_raise(404, "记录不存在")
    existing = await InterviewLike.aio_get_or_none(
        (InterviewLike.user == user.id) & (InterviewLike.interview == record_id)
    )
    if existing:
        await existing.aio_delete_instance()
        liked = False
    else:
        like = await InterviewLike.aio_create(user=user.id, interview=record_id)
        liked = True
        await notify_interview_like(record, user, int(like.id))
    cache_delete("share:feed:1:10")
    like_count = await (
        InterviewLike.select()
        .where(InterviewLike.interview == record_id)
        .aio_count()
    )
    return ok(
        data={"liked": liked, "like_count": like_count},
        message="操作成功",
    )


@router.post("/{record_id}/favorite")
async def toggle_favorite(
    record_id: int,
    user: User = Depends(get_current_user),
    _db=Depends(get_db),
):
    record = await InterviewRecord.aio_get_or_none(InterviewRecord.id == record_id)
    if not record:
        api_raise(404, "记录不存在")
    existing = await InterviewFavorite.aio_get_or_none(
        (InterviewFavorite.user == user.id) & (InterviewFavorite.interview == record_id)
    )
    if existing:
        await existing.aio_delete_instance()
        favorited = False
    else:
        await InterviewFavorite.aio_create(user=user.id, interview=record_id)
        favorited = True
    return ok(data={"favorited": favorited}, message="操作成功")


@router.get("/{record_id}/comments")
async def list_comments(
    record_id: int,
    limit: int = Query(3, ge=1, le=50),
    _db=Depends(get_db),
):
    total = await (
        InterviewComment.select()
        .where((InterviewComment.interview == record_id) & (InterviewComment.status == 1))
        .aio_count()
    )
    comments = list(
        await InterviewComment.select()
        .where((InterviewComment.interview == record_id) & (InterviewComment.status == 1))
        .order_by(InterviewComment.created_at.desc())
        .limit(limit)
        .aio_execute()
    )
    user_map: dict[int, User] = {}
    if comments:
        user_ids = list({c.user_id for c in comments})
        users = list(await User.select().where(User.id.in_(user_ids)).aio_execute())
        user_map = {u.id: u for u in users}
    items = [
        {
            "id": c.id,
            "user_id": c.user_id,
            "username": user_map.get(c.user_id).username if c.user_id in user_map else "",
            "avatar_url": enrich_media_url(
                user_map.get(c.user_id).avatar_url if c.user_id in user_map else None
            ),
            "content": c.content,
            "parent_id": c.parent_id,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in comments
    ]
    return ok(data={"items": items, "total": total}, message="查询成功")


@router.post("/{record_id}/comments")
async def create_comment(
    record_id: int,
    data: CommentCreate,
    user: User = Depends(get_current_user),
    _db=Depends(get_db),
):
    record = await InterviewRecord.aio_get_or_none(InterviewRecord.id == record_id)
    if not record:
        api_raise(404, "记录不存在")
    comment = await InterviewComment.aio_create(
        user=user.id,
        interview=record_id,
        content=data.content,
        parent=data.parent_id,
    )
    await notify_interview_comment(
        record, user, data.content, int(comment.id), data.parent_id
    )
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
async def update_comment(
    comment_id: int,
    data: CommentCreate,
    user: User = Depends(get_current_user),
    _db=Depends(get_db),
):
    c = await InterviewComment.aio_get_or_none(
        (InterviewComment.id == comment_id) & (InterviewComment.user == user.id)
    )
    if not c:
        api_raise(404, "评论不存在")
    c.content = data.content
    await c.aio_save()
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
async def delete_comment(
    comment_id: int, user: User = Depends(get_current_user), _db=Depends(get_db)
):
    c = await InterviewComment.aio_get_or_none(
        (InterviewComment.id == comment_id) & (InterviewComment.user == user.id)
    )
    if not c:
        api_raise(404, "评论不存在")
    c.status = 0
    await c.aio_save()
    return ok(message="删除成功")


@router.post("/comments/{comment_id}/report")
async def report_comment(
    comment_id: int, user: User = Depends(get_current_user), _db=Depends(get_db)
):
    c = await InterviewComment.aio_get_or_none(InterviewComment.id == comment_id)
    if not c:
        api_raise(404, "评论不存在")
    c.status = 2
    await c.aio_save()
    return ok(message="举报已提交")

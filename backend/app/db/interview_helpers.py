from __future__ import annotations

from collections import defaultdict
from typing import Optional

from app.models.interview import InterviewComment, InterviewFavorite, InterviewLike, InterviewRecord
from app.models.user import User
from app.services.storage import enrich_media_url


async def load_feed_relations(
    records: list[InterviewRecord],
) -> tuple[
    dict[int, list[InterviewLike]],
    dict[int, list[InterviewComment]],
    dict[int, list[InterviewFavorite]],
    dict[int, User],
]:
    """批量加载分享 feed 关联数据，避免 paginate + prefetch 在 MySQL 下生成非法 SQL。"""
    if not records:
        return {}, {}, {}, {}

    ids = [r.id for r in records]
    user_ids = list({int(r.user_id) for r in records})

    likes = list(
        await InterviewLike.select().where(InterviewLike.interview.in_(ids)).aio_execute()
    )
    comments = list(
        await InterviewComment.select()
        .where((InterviewComment.interview.in_(ids)) & (InterviewComment.status == 1))
        .aio_execute()
    )
    favorites = list(
        await InterviewFavorite.select()
        .where(InterviewFavorite.interview.in_(ids))
        .aio_execute()
    )
    users = list(await User.select().where(User.id.in_(user_ids)).aio_execute())

    likes_map: dict[int, list[InterviewLike]] = defaultdict(list)
    comments_map: dict[int, list[InterviewComment]] = defaultdict(list)
    favorites_map: dict[int, list[InterviewFavorite]] = defaultdict(list)
    for item in likes:
        likes_map[int(item.interview_id)].append(item)
    for item in comments:
        comments_map[int(item.interview_id)].append(item)
    for item in favorites:
        favorites_map[int(item.interview_id)].append(item)
    users_map = {u.id: u for u in users}
    return likes_map, comments_map, favorites_map, users_map


async def load_interview_social(
    interview_id: int,
) -> tuple[list[InterviewLike], list[InterviewComment], list[InterviewFavorite]]:
    likes = list(
        await InterviewLike.select()
        .where(InterviewLike.interview == interview_id)
        .aio_execute()
    )
    comments = list(
        await InterviewComment.select()
        .where(
            (InterviewComment.interview == interview_id)
            & (InterviewComment.status == 1)
        )
        .aio_execute()
    )
    favorites = list(
        await InterviewFavorite.select()
        .where(InterviewFavorite.interview == interview_id)
        .aio_execute()
    )
    return likes, comments, favorites


async def interview_to_dict(
    record: InterviewRecord,
    current: Optional[User] = None,
    *,
    likes: list[InterviewLike] | None = None,
    comments: list[InterviewComment] | None = None,
    favorites: list[InterviewFavorite] | None = None,
) -> dict:
    if likes is None or comments is None or favorites is None:
        likes, comments, favorites = await load_interview_social(record.id)

    like_count = len(likes)
    comment_count = len(comments)
    fav_count = len(favorites)
    current_id = current.id if current else None
    is_liked = bool(current_id and any(l.user_id == current_id for l in likes))
    is_fav = bool(current_id and any(f.user_id == current_id for f in favorites))

    return {
        "id": record.id,
        "user_id": record.user_id,
        "company_name": record.company_name,
        "job_title": record.job_title,
        "job_jd": record.job_jd,
        "remark": record.remark,
        "audio_url": enrich_media_url(record.audio_url),
        "interview_time": record.interview_time.isoformat() if record.interview_time else None,
        "ai_analysis": record.ai_analysis,
        "score": record.score,
        "ai_adopted": bool(record.ai_adopted),
        "visibility": record.visibility,
        "public_audio": record.public_audio,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        "like_count": like_count,
        "comment_count": comment_count,
        "favorite_count": fav_count,
        "is_liked": is_liked,
        "is_favorited": is_fav,
    }

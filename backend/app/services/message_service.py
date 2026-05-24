"""站内消息：评论、点赞等通知与历史回填"""

from __future__ import annotations

import datetime
import logging
from app.models.interview import InterviewComment, InterviewLike, InterviewRecord
from app.models.social import Message
from app.models.user import User

logger = logging.getLogger(__name__)


def _place_label(record: InterviewRecord) -> str:
    return f"{record.company_name} · {record.job_title}"


async def _message_exists(user_id: int, source_type: str, source_id: int) -> bool:
    return (
        await Message.aio_get_or_none(
            (Message.user == user_id)
            & (Message.source_type == source_type)
            & (Message.source_id == source_id)
        )
        is not None
    )


async def create_message_if_absent(
    *,
    user_id: int,
    title: str,
    content: str,
    msg_type: str,
    source_type: str,
    source_id: int,
    created_at: datetime.datetime | None = None,
) -> bool:
    """幂等创建消息，已存在则跳过。返回是否新建。"""
    if await _message_exists(user_id, source_type, source_id):
        return False
    kwargs: dict = {
        "user": user_id,
        "title": title[:100],
        "content": content,
        "msg_type": msg_type,
        "source_type": source_type,
        "source_id": source_id,
        "is_read": 0,
    }
    if created_at is not None:
        kwargs["created_at"] = created_at
    await Message.aio_create(**kwargs)
    return True


def _comment_recipient_ids(
    record: InterviewRecord,
    commenter_id: int,
    parent_user_id: int | None,
) -> set[int]:
    recipient_ids: set[int] = set()
    owner_id = int(record.user_id)
    if owner_id != commenter_id:
        recipient_ids.add(owner_id)
    if parent_user_id is not None and parent_user_id != commenter_id:
        recipient_ids.add(parent_user_id)
    return recipient_ids


async def notify_interview_comment(
    record: InterviewRecord,
    commenter: User,
    content: str,
    comment_id: int,
    parent_id: int | None = None,
) -> None:
    """评论/回复后通知帖子作者与被回复者（不通知评论者本人）。"""
    parent_user_id: int | None = None
    if parent_id:
        parent = await InterviewComment.aio_get_or_none(InterviewComment.id == parent_id)
        if parent:
            parent_user_id = int(parent.user_id)

    recipient_ids = _comment_recipient_ids(record, int(commenter.id), parent_user_id)
    if not recipient_ids:
        return

    preview = (content or "").strip()[:120]
    place = _place_label(record)
    for uid in recipient_ids:
        is_reply = parent_id and uid != int(record.user_id)
        title = (
            f"{commenter.username} 回复了你的评论"
            if is_reply
            else f"{commenter.username} 评论了你的面试分享"
        )
        await create_message_if_absent(
            user_id=uid,
            title=title,
            content=f"在「{place}」：{preview}",
            msg_type="comment",
            source_type="comment",
            source_id=comment_id,
        )


async def notify_interview_like(
    record: InterviewRecord,
    liker: User,
    like_id: int,
) -> None:
    """点赞后通知帖子作者（不通知自己）。"""
    if int(record.user_id) == int(liker.id):
        return
    place = _place_label(record)
    await create_message_if_absent(
        user_id=int(record.user_id),
        title=f"{liker.username} 赞了你的面试分享",
        content=f"「{place}」收到一个新赞",
        msg_type="like",
        source_type="like",
        source_id=like_id,
    )


async def backfill_social_messages() -> dict[str, int]:
    """为历史评论、点赞补建站内消息（幂等，可重复执行）。"""
    created = 0
    skipped = 0

    comments = list(
        await InterviewComment.select()
        .where(InterviewComment.status == 1)
        .order_by(InterviewComment.created_at.asc())
        .aio_execute()
    )
    likes = list(
        await InterviewLike.select()
        .order_by(InterviewLike.created_at.asc())
        .aio_execute()
    )

    interview_ids: set[int] = set()
    user_ids: set[int] = set()
    for c in comments:
        interview_ids.add(int(c.interview_id))
        user_ids.add(int(c.user_id))
    for lk in likes:
        interview_ids.add(int(lk.interview_id))
        user_ids.add(int(lk.user_id))

    records_map: dict[int, InterviewRecord] = {}
    if interview_ids:
        records = list(
            await InterviewRecord.select()
            .where(InterviewRecord.id.in_(list(interview_ids)))
            .aio_execute()
        )
        records_map = {int(r.id): r for r in records}
        for r in records:
            user_ids.add(int(r.user_id))

    users_map: dict[int, User] = {}
    if user_ids:
        users = list(await User.select().where(User.id.in_(list(user_ids))).aio_execute())
        users_map = {int(u.id): u for u in users}

    parent_ids = {int(c.parent_id) for c in comments if c.parent_id}
    parents_map: dict[int, InterviewComment] = {}
    if parent_ids:
        parents = list(
            await InterviewComment.select()
            .where(InterviewComment.id.in_(list(parent_ids)))
            .aio_execute()
        )
        parents_map = {int(p.id): p for p in parents}

    for c in comments:
        record = records_map.get(int(c.interview_id))
        commenter = users_map.get(int(c.user_id))
        if not record or not commenter:
            skipped += 1
            continue

        parent_user_id: int | None = None
        if c.parent_id:
            parent = parents_map.get(int(c.parent_id))
            if parent:
                parent_user_id = int(parent.user_id)

        recipient_ids = _comment_recipient_ids(record, int(commenter.id), parent_user_id)
        preview = (c.content or "").strip()[:120]
        place = _place_label(record)
        parent_id = int(c.parent_id) if c.parent_id else None

        for uid in recipient_ids:
            is_reply = parent_id and uid != int(record.user_id)
            title = (
                f"{commenter.username} 回复了你的评论"
                if is_reply
                else f"{commenter.username} 评论了你的面试分享"
            )
            if await create_message_if_absent(
                user_id=uid,
                title=title,
                content=f"在「{place}」：{preview}",
                msg_type="comment",
                source_type="comment",
                source_id=int(c.id),
                created_at=c.created_at,
            ):
                created += 1
            else:
                skipped += 1

    for lk in likes:
        record = records_map.get(int(lk.interview_id))
        liker = users_map.get(int(lk.user_id))
        if not record or not liker:
            skipped += 1
            continue
        if int(record.user_id) == int(liker.id):
            skipped += 1
            continue
        place = _place_label(record)
        if await create_message_if_absent(
            user_id=int(record.user_id),
            title=f"{liker.username} 赞了你的面试分享",
            content=f"「{place}」收到一个新赞",
            msg_type="like",
            source_type="like",
            source_id=int(lk.id),
            created_at=lk.created_at,
        ):
            created += 1
        else:
            skipped += 1

    return {"created": created, "skipped": skipped}

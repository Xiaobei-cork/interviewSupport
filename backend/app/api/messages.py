from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.social import Message
from app.core.response import ok

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("")
async def list_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    _db=Depends(get_db),
):
    q = Message.select().where(Message.user == user.id)
    total = await q.aio_count()
    items = list(
        await q.order_by(Message.created_at.desc()).paginate(page, page_size).aio_execute()
    )
    return ok(
        data={
            "items": [
                {
                    "id": m.id,
                    "title": m.title,
                    "content": m.content,
                    "msg_type": m.msg_type,
                    "is_read": m.is_read,
                    "created_at": m.created_at.isoformat(),
                }
                for m in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        message="查询成功",
    )


@router.get("/unread-count")
async def unread_count(user: User = Depends(get_current_user), _db=Depends(get_db)):
    count = await (
        Message.select()
        .where((Message.user == user.id) & (Message.is_read == 0))
        .aio_count()
    )
    return ok(data={"count": count}, message="查询成功")


@router.put("/{msg_id}/read")
async def mark_read(msg_id: int, user: User = Depends(get_current_user), _db=Depends(get_db)):
    m = await Message.aio_get_or_none((Message.id == msg_id) & (Message.user == user.id))
    if m:
        m.is_read = 1
        await m.aio_save()
    return ok(message="已读")

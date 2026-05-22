from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.social import Message
from app.core.response import ok

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("")
def list_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Message).filter(Message.user_id == user.id)
    total = q.count()
    items = q.order_by(Message.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
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
def unread_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    count = db.query(Message).filter(Message.user_id == user.id, Message.is_read == 0).count()
    return ok(data={"count": count}, message="查询成功")


@router.put("/{msg_id}/read")
def mark_read(msg_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    m = db.query(Message).filter(Message.id == msg_id, Message.user_id == user.id).first()
    if m:
        m.is_read = 1
        db.commit()
    return ok(message="已读")

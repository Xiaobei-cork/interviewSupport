from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.social import UserFriend
from app.core.response import ok, api_raise

router = APIRouter(prefix="/friends", tags=["friends"])


@router.post("/request")
def request_friend(friend_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if friend_id == user.id:
        api_raise(400, "不能添加自己")
    target = db.query(User).filter(User.id == friend_id).first()
    if not target:
        api_raise(404, "用户不存在")
    existing = (
        db.query(UserFriend)
        .filter(
            ((UserFriend.user_id == user.id) & (UserFriend.friend_id == friend_id))
            | ((UserFriend.user_id == friend_id) & (UserFriend.friend_id == user.id))
        )
        .first()
    )
    if existing:
        api_raise(400, "已是好友或已发送请求")
    db.add(UserFriend(user_id=user.id, friend_id=friend_id, status="pending"))
    db.commit()
    return ok(message="好友请求已发送")


@router.put("/{friendship_id}/accept")
def accept_friend(friendship_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    f = db.query(UserFriend).filter(UserFriend.id == friendship_id, UserFriend.friend_id == user.id).first()
    if not f:
        api_raise(404, "好友请求不存在")
    f.status = "accepted"
    reverse = UserFriend(user_id=user.id, friend_id=f.user_id, status="accepted")
    if not db.query(UserFriend).filter(
        UserFriend.user_id == user.id, UserFriend.friend_id == f.user_id
    ).first():
        db.add(reverse)
    db.commit()
    return ok(message="已接受好友请求")

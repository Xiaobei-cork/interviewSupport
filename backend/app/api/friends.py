from fastapi import APIRouter, Depends

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.social import UserFriend
from app.core.response import ok, api_raise

router = APIRouter(prefix="/friends", tags=["friends"])


@router.post("/request")
async def request_friend(
    friend_id: int, user: User = Depends(get_current_user), _db=Depends(get_db)
):
    if friend_id == user.id:
        api_raise(400, "不能添加自己")
    target = await User.aio_get_or_none(User.id == friend_id)
    if not target:
        api_raise(404, "用户不存在")
    existing = await UserFriend.aio_get_or_none(
        ((UserFriend.user == user.id) & (UserFriend.friend == friend_id))
        | ((UserFriend.user == friend_id) & (UserFriend.friend == user.id))
    )
    if existing:
        api_raise(400, "已是好友或已发送请求")
    await UserFriend.aio_create(user=user.id, friend=friend_id, status="pending")
    return ok(message="好友请求已发送")


@router.put("/{friendship_id}/accept")
async def accept_friend(
    friendship_id: int, user: User = Depends(get_current_user), _db=Depends(get_db)
):
    f = await UserFriend.aio_get_or_none(
        (UserFriend.id == friendship_id) & (UserFriend.friend == user.id)
    )
    if not f:
        api_raise(404, "好友请求不存在")
    f.status = "accepted"
    await f.aio_save()
    if not await UserFriend.aio_get_or_none(
        (UserFriend.user == user.id) & (UserFriend.friend == f.user_id)
    ):
        await UserFriend.aio_create(user=user.id, friend=f.user_id, status="accepted")
    return ok(message="已接受好友请求")

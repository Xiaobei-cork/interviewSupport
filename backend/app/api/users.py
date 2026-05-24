import logging

from fastapi import APIRouter, Depends, UploadFile, File

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserUpdate, PasswordUpdate
from app.core.response import ok, api_raise
from app.services.storage import save_file, enrich_media_url
from app.utils.security import verify_password, hash_password

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger("app.users")

PRESET_AVATARS = [f"/api/v1/static/avatars/avatar_{i}.svg" for i in range(1, 13)]


def _user_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "account": user.account,
        "phone": user.phone,
        "email": user.email,
        "avatar_url": enrich_media_url(user.avatar_url),
        "address": user.address,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return ok(data=_user_dict(user), message="获取成功")


@router.put("/me")
async def update_me(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    _db=Depends(get_db),
):
    payload = data.model_dump(exclude_unset=True)
    if payload.get("phone"):
        exists = await User.aio_get_or_none(
            (User.phone == payload["phone"]) & (User.id != user.id)
        )
        if exists:
            api_raise(400, "该手机号已被其他账号使用")
    if payload.get("email"):
        exists = await User.aio_get_or_none(
            (User.email == payload["email"]) & (User.id != user.id)
        )
        if exists:
            api_raise(400, "该邮箱已被其他账号使用")
    for k, v in payload.items():
        setattr(user, k, v)
    await user.aio_save()
    logger.info("用户资料更新 id=%s", user.id)
    return ok(data=_user_dict(user), message="保存成功")


@router.put("/me/password")
async def change_password(
    data: PasswordUpdate,
    user: User = Depends(get_current_user),
    _db=Depends(get_db),
):
    if not verify_password(data.old_password, user.password):
        api_raise(400, "旧密码不正确")
    user.password = hash_password(data.new_password)
    await user.aio_save()
    logger.info("用户修改密码 id=%s", user.id)
    return ok(message="密码修改成功")


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    _db=Depends(get_db),
):
    user.avatar_url = save_file(file.file, file.filename or "avatar.png", "avatars")
    await user.aio_save()
    return ok(data=_user_dict(user), message="头像上传成功")


@router.get("/avatars/presets")
async def get_preset_avatars():
    return ok(data={"avatars": PRESET_AVATARS}, message="获取成功")

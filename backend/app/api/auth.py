import logging
import random
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin
from app.core.response import ok, created, api_raise
from app.utils.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("app.auth")


@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    if not data.phone and not data.email:
        api_raise(400, "请提供手机号或邮箱")
    if db.query(User).filter(User.account == data.account).first():
        api_raise(400, "该账号已被注册，请更换账号")
    if data.phone and db.query(User).filter(User.phone == data.phone).first():
        api_raise(400, "该手机号已被注册")
    if data.email and db.query(User).filter(User.email == data.email).first():
        api_raise(400, "该邮箱已被注册")
    username = f"用户{random.randint(10000, 99999)}"
    user = User(
        username=username,
        account=data.account,
        password=hash_password(data.password),
        phone=data.phone,
        email=data.email,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(str(user.id))
    logger.info("用户注册成功 account=%s id=%s", data.account, user.id)
    return created(
        data={"access_token": token, "token_type": "bearer"},
        message="注册成功",
    )


@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.account == data.account).first()
    if not user or not verify_password(data.password, user.password):
        logger.warning("登录失败 account=%s", data.account)
        api_raise(401, "账号或密码错误")
    token = create_access_token(str(user.id))
    logger.info("用户登录成功 account=%s id=%s", data.account, user.id)
    return ok(
        data={"access_token": token, "token_type": "bearer"},
        message="登录成功",
    )

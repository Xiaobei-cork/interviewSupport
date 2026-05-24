from __future__ import annotations

from typing import AsyncIterator
from urllib.parse import parse_qs, unquote, urlparse

from peewee_async import MySQLDatabase, SqliteDatabase

from app.config import get_settings

ALL_MODELS: list[type] = []


def _register_models() -> None:
    from app.models.user import User
    from app.models.interview import (
        InterviewComment,
        InterviewFavorite,
        InterviewLike,
        InterviewRecord,
    )
    from app.models.resume import Resume
    from app.models.social import Message, UserFriend

    global ALL_MODELS
    ALL_MODELS = [
        User,
        InterviewRecord,
        InterviewLike,
        InterviewFavorite,
        InterviewComment,
        Resume,
        UserFriend,
        Message,
    ]


def parse_database_url(url: str) -> dict:
    """Parse mysql+pymysql:// or sqlite:// style URLs for peewee-async."""
    normalized = url.replace("mysql+pymysql://", "mysql://").replace(
        "mysql+pool+async://", "mysql://"
    )
    if normalized.startswith("sqlite"):
        path = normalized.split("://", 1)[-1]
        if path in ("", "/:memory:", ":memory:"):
            return {
                "driver": "sqlite",
                "database": "file::memory:?cache=shared",
                "uri": True,
            }
        return {"driver": "sqlite", "database": path.lstrip("/"), "uri": False}

    parsed = urlparse(normalized)
    db_name = parsed.path.lstrip("/").split("?")[0]
    qs = parse_qs(parsed.query)
    charset = (qs.get("charset") or ["utf8mb4"])[0]
    return {
        "driver": "mysql",
        "database": db_name,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "host": parsed.hostname or "localhost",
        "port": int(parsed.port or 3306),
        "charset": charset,
    }


def create_database(url: str | None = None) -> MySQLDatabase | SqliteDatabase:
    params = parse_database_url(url or get_settings().database_url)
    if params["driver"] == "sqlite":
        return SqliteDatabase(params["database"], uri=params.get("uri", False))
    return MySQLDatabase(
        params["database"],
        user=params["user"],
        password=params["password"],
        host=params["host"],
        port=params["port"],
        charset=params["charset"],
        pool_params={"maxsize": 20, "minsize": 1, "pool_recycle": 3600},
    )


database = create_database()


def bind_models(db: MySQLDatabase | SqliteDatabase) -> None:
    _register_models()
    for model in ALL_MODELS:
        model._meta.database = db


bind_models(database)


async def connect_db() -> None:
    await database.aio_connect()


async def close_db() -> None:
    await database.aio_close()


async def get_db() -> AsyncIterator[MySQLDatabase | SqliteDatabase]:
    async with database.aio_connection():
        yield database

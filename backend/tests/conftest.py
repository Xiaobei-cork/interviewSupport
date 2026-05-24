import asyncio
import os

import pytest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from app.config import get_settings

get_settings.cache_clear()

import app.database as db_module
from app.database import ALL_MODELS, bind_models, create_database, connect_db, close_db

test_database = create_database(os.environ["DATABASE_URL"])
db_module.database = test_database
bind_models(test_database)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database(event_loop):
    async def _setup():
        await connect_db()
        await test_database.aio_create_tables(ALL_MODELS)

    async def _teardown():
        await close_db()

    event_loop.run_until_complete(_setup())
    yield
    event_loop.run_until_complete(_teardown())

import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from app.config import get_settings

get_settings.cache_clear()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import app.database as db

settings = get_settings()
test_engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
db.engine = test_engine
db.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

from app.database import Base

Base.metadata.create_all(bind=test_engine)

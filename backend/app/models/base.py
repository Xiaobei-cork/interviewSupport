from peewee_async import AioModel

from app.database import database


class BaseModel(AioModel):
    class Meta:
        database = database

import datetime

from peewee import (
    BigIntegerField,
    CharField,
    DateTimeField,
    FloatField,
    ForeignKeyField,
    SmallIntegerField,
    TextField,
)

from app.models.base import BaseModel
from app.models.user import User


class Resume(BaseModel):
    class Meta:
        table_name = "resume"

    id = BigIntegerField(primary_key=True)
    user = ForeignKeyField(User, backref="resumes", column_name="user_id", index=True)
    file_name = CharField(max_length=100)
    file_url = CharField(max_length=255)
    file_type = CharField(max_length=10)
    ai_analysis = TextField(null=True)
    score = FloatField(null=True)
    ai_adopted = SmallIntegerField(default=0)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

import datetime

from peewee import (
    BigIntegerField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    SmallIntegerField,
    TextField,
)

from app.models.base import BaseModel
from app.models.user import User


class UserFriend(BaseModel):
    class Meta:
        table_name = "user_friend"
        indexes = ((("user_id", "friend_id"), True),)

    id = BigIntegerField(primary_key=True)
    user = ForeignKeyField(User, column_name="user_id")
    friend = ForeignKeyField(User, backref="friend_of", column_name="friend_id")
    status = CharField(max_length=20, default="accepted")
    created_at = DateTimeField(default=datetime.datetime.now)


class Message(BaseModel):
    class Meta:
        table_name = "message"
        indexes = ((("user_id", "source_type", "source_id"), True),)

    id = BigIntegerField(primary_key=True)
    user = ForeignKeyField(User, backref="messages", column_name="user_id", index=True)
    title = CharField(max_length=100)
    content = TextField()
    msg_type = CharField(max_length=30, default="system")
    source_type = CharField(max_length=20, null=True)
    source_id = BigIntegerField(null=True)
    is_read = SmallIntegerField(default=0)
    created_at = DateTimeField(default=datetime.datetime.now)

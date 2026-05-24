import datetime

from peewee import BigIntegerField, CharField, DateTimeField

from app.models.base import BaseModel


class User(BaseModel):
    class Meta:
        table_name = "users"

    id = BigIntegerField(primary_key=True)
    username = CharField(max_length=50)
    account = CharField(max_length=50, unique=True, index=True)
    password = CharField(max_length=255)
    phone = CharField(max_length=20, null=True)
    email = CharField(max_length=50, null=True)
    avatar_url = CharField(max_length=255, null=True)
    address = CharField(max_length=255, null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

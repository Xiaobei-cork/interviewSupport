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


class InterviewRecord(BaseModel):
    class Meta:
        table_name = "interview_record"

    id = BigIntegerField(primary_key=True)
    user = ForeignKeyField(User, backref="interviews", column_name="user_id", index=True)
    company_name = CharField(max_length=100)
    job_title = CharField(max_length=100)
    job_jd = TextField(null=True)
    remark = TextField(null=True)
    audio_url = CharField(max_length=255, null=True)
    interview_time = DateTimeField()
    ai_analysis = TextField(null=True)
    score = FloatField(null=True)
    ai_adopted = SmallIntegerField(default=0)
    visibility = SmallIntegerField(default=1)
    public_audio = SmallIntegerField(default=0)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)


class InterviewLike(BaseModel):
    class Meta:
        table_name = "interview_like"
        indexes = ((("user_id", "interview_id"), True),)

    id = BigIntegerField(primary_key=True)
    user = ForeignKeyField(User, column_name="user_id")
    interview = ForeignKeyField(InterviewRecord, backref="likes", column_name="interview_id")
    created_at = DateTimeField(default=datetime.datetime.now)


class InterviewFavorite(BaseModel):
    class Meta:
        table_name = "interview_favorite"
        indexes = ((("user_id", "interview_id"), True),)

    id = BigIntegerField(primary_key=True)
    user = ForeignKeyField(User, column_name="user_id")
    interview = ForeignKeyField(InterviewRecord, backref="favorites", column_name="interview_id")
    created_at = DateTimeField(default=datetime.datetime.now)


class InterviewComment(BaseModel):
    class Meta:
        table_name = "interview_comment"

    id = BigIntegerField(primary_key=True)
    user = ForeignKeyField(User, backref="comments", column_name="user_id")
    interview = ForeignKeyField(InterviewRecord, backref="comments", column_name="interview_id")
    parent = ForeignKeyField("self", null=True, backref="replies", column_name="parent_id")
    content = TextField()
    status = SmallIntegerField(default=1)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

from app.models.user import User
from app.models.interview import InterviewRecord, InterviewLike, InterviewFavorite, InterviewComment
from app.models.resume import Resume
from app.models.social import UserFriend, Message

__all__ = [
    "User",
    "InterviewRecord",
    "InterviewLike",
    "InterviewFavorite",
    "InterviewComment",
    "Resume",
    "UserFriend",
    "Message",
]

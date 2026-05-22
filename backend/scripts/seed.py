"""Seed demo data. Run: python -m scripts.seed (from backend dir)"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.user import User
from app.models.interview import InterviewRecord
from app.models.social import Message
from app.utils.security import hash_password


def seed():
    db = SessionLocal()
    if db.query(User).filter(User.account == "demo").first():
        print("Seed data already exists")
        db.close()
        return

    user = User(
        username="用户12345",
        account="demo",
        password=hash_password("demo123"),
        phone="13800138000",
        email="demo@example.com",
        avatar_url="/api/v1/static/avatars/avatar_1.svg",
    )
    db.add(user)
    db.flush()

    companies = [
        ("字节跳动", "后端开发工程师"),
        ("阿里巴巴", "Java开发工程师"),
        ("腾讯", "全栈工程师"),
        ("美团", "服务端工程师"),
        ("华为", "软件工程师"),
    ]
    for i, (company, job) in enumerate(companies):
        db.add(
            InterviewRecord(
                user_id=user.id,
                company_name=company,
                job_title=job,
                job_jd=f"负责{job}相关工作，熟悉Python/Java，有分布式系统经验。",
                remark="面试表现良好",
                interview_time=datetime.now() - timedelta(days=i + 1),
                visibility=1 if i < 4 else 0,
                public_audio=1 if i == 0 else 0,
                score=4.0 - i * 0.3,
            )
        )

    db.add(
        Message(
            user_id=user.id,
            title="欢迎使用面试助手",
            content="您可以开始记录面试复盘，并使用AI分析功能。",
            msg_type="system",
            is_read=0,
        )
    )
    db.add(
        Message(
            user_id=user.id,
            title="系统通知",
            content="您的第一条面试记录已创建成功。",
            msg_type="system",
            is_read=1,
        )
    )
    db.commit()
    print("Seed complete: account=demo password=demo123")
    db.close()


if __name__ == "__main__":
    seed()

"""为历史评论、点赞补建站内消息。Run: python -m scripts.backfill_messages (from backend dir)"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import connect_db, close_db, database
from app.services.message_service import backfill_social_messages


async def main() -> None:
    await connect_db()
    try:
        async with database.aio_connection():
            stats = await backfill_social_messages()
            print(
                f"回填完成：新建 {stats['created']} 条，跳过 {stats['skipped']} 条（已存在或无接收人）"
            )
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())

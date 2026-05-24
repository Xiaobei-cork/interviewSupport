import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, UploadFile, File, BackgroundTasks
from app.database import database, get_db
from app.api.deps import get_current_user, get_current_user_optional
from app.db.interview_helpers import interview_to_dict
from app.models.user import User
from app.models.interview import InterviewRecord
from app.schemas.interview import InterviewCreate, InterviewUpdate, ScoreUpdate, AiAdoptRequest, AiChatRequest
from app.core.response import ok, created, api_raise
from app.services.storage import save_file
from app.services import ai_service
from app.services.task_service import run_task, create_task, get_task

router = APIRouter(prefix="/interviews", tags=["interviews"])
logger = logging.getLogger("app.interviews")


@router.get("")
async def list_interviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    visibility: Optional[int] = None,
    keyword: Optional[str] = None,
    user: User = Depends(get_current_user),
    _db=Depends(get_db),
):
    q = InterviewRecord.select().where(InterviewRecord.user == user.id)
    if visibility is not None:
        q = q.where(InterviewRecord.visibility == visibility)
    if keyword:
        q = q.where(
            (InterviewRecord.company_name.contains(keyword))
            | (InterviewRecord.job_title.contains(keyword))
        )
    total = await q.aio_count()
    items = list(
        await q.order_by(InterviewRecord.interview_time.desc())
        .paginate(page, page_size)
        .aio_execute()
    )
    return ok(
        data={
            "items": [await interview_to_dict(i, user) for i in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        message="查询成功",
    )


@router.post("")
async def create_interview(
    data: InterviewCreate,
    user: User = Depends(get_current_user),
    _db=Depends(get_db),
):
    payload = data.model_dump()
    record = await InterviewRecord.aio_create(user=user.id, **payload)
    logger.info("创建面试记录 user=%s id=%s", user.id, record.id)
    return created(data=await interview_to_dict(record, user), message="创建成功")


@router.get("/{record_id}")
async def get_interview(
    record_id: int,
    user: Optional[User] = Depends(get_current_user_optional),
    _db=Depends(get_db),
):
    record = await InterviewRecord.aio_get_or_none(InterviewRecord.id == record_id)
    if not record:
        api_raise(404, "记录不存在")
    if record.user_id != (user.id if user else -1) and record.visibility != 1:
        api_raise(403, "无权访问")
    return ok(data=await interview_to_dict(record, user), message="获取成功")


@router.put("/{record_id}")
async def update_interview(
    record_id: int,
    data: InterviewUpdate,
    user: User = Depends(get_current_user),
    _db=Depends(get_db),
):
    record = await InterviewRecord.aio_get_or_none(
        (InterviewRecord.id == record_id) & (InterviewRecord.user == user.id)
    )
    if not record:
        api_raise(404, "记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(record, k, v)
    await record.aio_save()
    return ok(data=await interview_to_dict(record, user), message="更新成功")


@router.delete("/{record_id}")
async def delete_interview(
    record_id: int,
    user: User = Depends(get_current_user),
    _db=Depends(get_db),
):
    record = await InterviewRecord.aio_get_or_none(
        (InterviewRecord.id == record_id) & (InterviewRecord.user == user.id)
    )
    if not record:
        api_raise(404, "记录不存在")
    await record.aio_delete_instance(recursive=True)
    return ok(message="删除成功")


@router.post("/{record_id}/audio")
async def upload_audio(
    record_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    _db=Depends(get_db),
):
    record = await InterviewRecord.aio_get_or_none(
        (InterviewRecord.id == record_id) & (InterviewRecord.user == user.id)
    )
    if not record:
        api_raise(404, "记录不存在")
    ext = (file.filename or "").lower()
    if not any(ext.endswith(e) for e in [".mp3", ".wav", ".m4a"]):
        api_raise(400, "仅支持 mp3/wav/m4a")
    record.audio_url = save_file(file.file, file.filename or "audio.mp3", "audio")
    await record.aio_save()
    return ok(data=await interview_to_dict(record, user), message="上传成功")


@router.post("/{record_id}/ai/analyze")
async def start_ai_analyze(
    record_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    _db=Depends(get_db),
):
    record = await InterviewRecord.aio_get_or_none(
        (InterviewRecord.id == record_id) & (InterviewRecord.user == user.id)
    )
    if not record:
        api_raise(404, "记录不存在")
    if record.ai_adopted:
        api_raise(400, "已采纳 AI 分析，不可重新分析")

    task_id = create_task()
    record_id_copy = record.id

    async def worker():
        async with database.aio_connection():
            rec = await InterviewRecord.aio_get_or_none(InterviewRecord.id == record_id_copy)
            if not rec:
                return {"overall": "记录不存在"}
            has_audio = bool(rec.audio_url)
            transcript = ""
            if has_audio:
                transcript = (
                    "（已上传录音文件，当前系统未配置语音转写服务，"
                    "不得编造任何面试问答；请结合岗位名称、岗位 JD、备注给出分析与建议。）"
                )
            result = await ai_service.analyze_interview(
                company_name=rec.company_name,
                job_title=rec.job_title,
                job_jd=rec.job_jd or "",
                remark=rec.remark or "",
                transcript=transcript,
                has_audio=has_audio,
            )
            rec.ai_analysis = json.dumps(result, ensure_ascii=False)
            rec.ai_adopted = 0
            if result.get("score") is not None:
                rec.score = float(result["score"])
            await rec.aio_save()
            return result

    background_tasks.add_task(run_task, task_id, worker)
    return ok(data={"task_id": task_id}, message="分析任务已提交")


@router.get("/ai/tasks/{task_id}")
async def poll_task(task_id: str):
    task = get_task(task_id)
    if not task:
        api_raise(404, "任务不存在")
    return ok(data=task, message="查询成功")


@router.post("/{record_id}/ai/adopt")
async def adopt_ai_analysis(
    record_id: int,
    data: AiAdoptRequest,
    user: User = Depends(get_current_user),
    _db=Depends(get_db),
):
    record = await InterviewRecord.aio_get_or_none(
        (InterviewRecord.id == record_id) & (InterviewRecord.user == user.id)
    )
    if not record:
        api_raise(404, "记录不存在")
    if not record.ai_analysis:
        api_raise(400, "请先完成 AI 分析后再采纳")
    if data.score is not None:
        record.score = float(data.score)
    elif record.score is None:
        try:
            parsed = json.loads(record.ai_analysis)
            if parsed.get("score") is not None:
                record.score = float(parsed["score"])
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    record.ai_adopted = 1
    await record.aio_save()
    return ok(data=await interview_to_dict(record, user), message="已采纳 AI 分析")


@router.put("/{record_id}/score")
async def update_score(
    record_id: int,
    data: ScoreUpdate,
    user: User = Depends(get_current_user),
    _db=Depends(get_db),
):
    record = await InterviewRecord.aio_get_or_none(
        (InterviewRecord.id == record_id) & (InterviewRecord.user == user.id)
    )
    if not record:
        api_raise(404, "记录不存在")
    record.score = data.score
    await record.aio_save()
    return ok(data=await interview_to_dict(record, user), message="评分已保存")


@router.post("/{record_id}/ai/chat")
async def ai_chat(
    record_id: int,
    data: AiChatRequest,
    user: User = Depends(get_current_user),
    _db=Depends(get_db),
):
    record = await InterviewRecord.aio_get_or_none(
        (InterviewRecord.id == record_id) & (InterviewRecord.user == user.id)
    )
    if not record:
        api_raise(404, "记录不存在")
    parts = [
        f"公司：{record.company_name}",
        f"岗位：{record.job_title}",
        f"JD：{record.job_jd or '（无）'}",
        f"备注：{record.remark or '（无）'}",
        f"录音：{'已上传' if record.audio_url else '无'}",
    ]
    if record.ai_analysis:
        parts.append(f"AI分析结果：{record.ai_analysis}")
    context = "\n".join(parts)
    reply = await ai_service.chat_interview(context, data.message)
    return ok(data={"reply": reply}, message="success")

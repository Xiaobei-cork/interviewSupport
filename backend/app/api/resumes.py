import json
import logging
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, Query, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.resume import Resume
from app.schemas.interview import AiChatRequest
from app.schemas.resume import ResumeAiAdoptRequest, ResumeDeepOptimizeRequest, ResumeSaveOptimizedRequest
from app.core.response import ok, created, api_raise
from app.services.storage import save_file, open_as_path, file_inline_response, file_download_response, enrich_media_url
from app.services import ai_service, resume_parser
from app.services.task_service import run_task, create_task, get_task

router = APIRouter(prefix="/resumes", tags=["resumes"])
logger = logging.getLogger("app.resumes")


def _resume_dict(r: Resume) -> dict:
    return {
        "id": r.id,
        "user_id": r.user_id,
        "file_name": r.file_name,
        "file_url": enrich_media_url(r.file_url),
        "file_type": r.file_type,
        "ai_analysis": r.ai_analysis,
        "score": r.score,
        "ai_adopted": bool(r.ai_adopted),
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


def _file_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in (".doc", ".docx"):
        return "word"
    api_raise(400, "仅支持 Word/PDF")


@router.get("")
def list_resumes(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    file_type: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Resume).filter(Resume.user_id == user.id)
    if file_type and file_type != "all":
        q = q.filter(Resume.file_type == file_type)
    total = q.count()
    items = q.order_by(Resume.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ok(
        data={
            "items": [_resume_dict(i) for i in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        message="查询成功",
    )


@router.post("")
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ft = _file_type(file.filename or "")
    url = save_file(file.file, file.filename or "resume.pdf", "resumes")
    resume = Resume(
        user_id=user.id,
        file_name=file.filename or "resume",
        file_url=url,
        file_type=ft,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return created(data=_resume_dict(resume), message="上传成功")


@router.get("/{resume_id}")
def get_resume(resume_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user.id).first()
    if not r:
        api_raise(404, "简历不存在")
    return ok(data=_resume_dict(r), message="获取成功")


@router.delete("/{resume_id}")
def delete_resume(resume_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user.id).first()
    if not r:
        api_raise(404, "简历不存在")
    db.delete(r)
    db.commit()
    return ok(message="删除成功")


@router.get("/{resume_id}/preview")
def preview_resume(resume_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user.id).first()
    if not r:
        api_raise(404, "简历不存在")
    try:
        return file_inline_response(r.file_url, r.file_name)
    except FileNotFoundError:
        api_raise(404, "文件不存在")


@router.post("/{resume_id}/ai/analyze")
def analyze_resume(
    resume_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user.id).first()
    if not r:
        api_raise(404, "简历不存在")
    if r.ai_adopted:
        api_raise(400, "已采纳 AI 分析，不可重新分析")
    task_id = create_task()
    resume_id_copy = r.id
    file_url = r.file_url
    file_type = r.file_type

    async def worker():
        from app.database import SessionLocal
        text = "示例简历内容：计算机专业，3年后端开发经验。"
        try:
            with open_as_path(file_url) as (path, _):
                text = resume_parser.extract_text(path, file_type)
        except FileNotFoundError:
            logger.warning("简历文件无法读取 resume_id=%s url=%s", resume_id_copy, file_url)
        result = await ai_service.analyze_resume(text)
        sess = SessionLocal()
        try:
            rec = sess.query(Resume).filter(Resume.id == resume_id_copy).first()
            if rec:
                rec.ai_analysis = json.dumps(result, ensure_ascii=False)
                rec.ai_adopted = 0
                if result.get("score") is not None:
                    rec.score = float(result["score"])
                sess.commit()
        finally:
            sess.close()
        return result

    background_tasks.add_task(run_task, task_id, worker)
    return ok(data={"task_id": task_id}, message="分析任务已提交")


@router.post("/{resume_id}/ai/adopt")
def adopt_resume_ai(
    resume_id: int,
    data: ResumeAiAdoptRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user.id).first()
    if not r:
        api_raise(404, "简历不存在")
    if not r.ai_analysis:
        api_raise(400, "请先完成 AI 分析后再采纳")
    if data.score is not None:
        r.score = float(data.score)
    elif r.score is None:
        try:
            parsed = json.loads(r.ai_analysis)
            if isinstance(parsed, dict) and parsed.get("score") is not None:
                r.score = float(parsed["score"])
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    r.ai_adopted = 1
    db.commit()
    db.refresh(r)
    return ok(data=_resume_dict(r), message="已采纳 AI 分析")


@router.get("/ai/tasks/{task_id}")
def poll_resume_task(task_id: str):
    task = get_task(task_id)
    if not task:
        api_raise(404, "任务不存在")
    return ok(data=task, message="查询成功")


@router.post("/{resume_id}/ai/deep-optimize")
async def deep_optimize_resume_api(
    resume_id: int,
    data: ResumeDeepOptimizeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user.id).first()
    if not r:
        api_raise(404, "简历不存在")
    text = "示例简历内容：计算机专业，3年后端开发经验。"
    try:
        with open_as_path(r.file_url) as (path, _):
            text = resume_parser.extract_text(path, r.file_type)
    except FileNotFoundError:
        logger.warning("深度优化无法读取简历 resume_id=%s", resume_id)
    result = await ai_service.deep_optimize_resume(text, data.requirement)
    preview = result.get("preview") or result
    logger.info("简历深度优化 resume_id=%s", resume_id)
    return ok(data={"preview": preview}, message="优化完成")


@router.put("/{resume_id}/optimized-preview")
def save_optimized_preview(
    resume_id: int,
    data: ResumeSaveOptimizedRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user.id).first()
    if not r:
        api_raise(404, "简历不存在")
    stored: dict = {}
    if r.ai_analysis:
        try:
            stored = json.loads(r.ai_analysis)
            if not isinstance(stored, dict):
                stored = {"analysis": stored}
        except Exception:
            stored = {"legacy": r.ai_analysis}
    stored["optimized_preview"] = data.preview.model_dump()
    r.ai_analysis = json.dumps(stored, ensure_ascii=False)
    db.commit()
    return ok(message="优化内容已保存")


@router.post("/{resume_id}/ai/chat")
async def resume_chat(
    resume_id: int,
    data: AiChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user.id).first()
    if not r:
        api_raise(404, "简历不存在")
    ctx = r.ai_analysis or f"简历文件名：{r.file_name}（暂无解析正文）"
    reply = await ai_service.chat_resume(ctx, data.message)
    return ok(data={"reply": reply}, message="success")


@router.get("/{resume_id}/export")
def export_resume(
    resume_id: int,
    format: str = Query("pdf"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user.id).first()
    if not r:
        api_raise(404, "简历不存在")
    try:
        return file_download_response(r.file_url, r.file_name)
    except FileNotFoundError:
        api_raise(404, "文件不存在")

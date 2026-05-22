from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.config import get_settings
from app.core.response import api_raise

router = APIRouter(tags=["files"])
settings = get_settings()


@router.get("/files/{subdir}/{filename}")
def serve_file(subdir: str, filename: str):
    path = Path(settings.upload_dir) / subdir / filename
    if not path.exists() or ".." in subdir or ".." in filename:
        api_raise(404, "文件不存在")
    return FileResponse(path)

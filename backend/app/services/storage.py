import logging
import mimetypes
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator
from urllib.parse import urlparse

from app.config import get_settings

logger = logging.getLogger("app.storage")

def _get_bucket():
    import oss2

    s = get_settings()
    auth = oss2.Auth(s.oss_access_key_id, s.oss_access_key_secret)
    return oss2.Bucket(auth, s.oss_endpoint, s.oss_bucket)


def _ensure_dir(subdir: str) -> Path:
    base = Path(get_settings().upload_dir) / subdir
    base.mkdir(parents=True, exist_ok=True)
    return base


def is_local_url(url: str) -> bool:
    return bool(url) and url.startswith("/api/v1/files/")


def is_oss_ref(url: str) -> bool:
    if not url:
        return False
    if url.startswith("oss://"):
        return True
    if not url.startswith(("http://", "https://")):
        return False
    s = get_settings()
    host = urlparse(url).netloc.lower()
    bucket = s.oss_bucket.lower()
    endpoint = s.oss_endpoint.lower().split("/")[0]
    cdn = (s.oss_cdn_domain or "").lower()
    return bucket in host or endpoint in host or (cdn and cdn in host)


def oss_key_from_ref(ref: str) -> str:
    if ref.startswith("oss://"):
        return ref[6:]
    path = urlparse(ref).path.lstrip("/")
    return path


def save_file(file_data: BinaryIO, filename: str, subdir: str) -> str:
    ext = Path(filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    content = file_data.read()

    if get_settings().oss_enabled:
        key = f"{subdir}/{unique_name}"
        _get_bucket().put_object(key, content)
        logger.info("OSS 上传成功 key=%s", key)
        return f"oss://{key}"

    dest_dir = _ensure_dir(subdir)
    dest_path = dest_dir / unique_name
    dest_path.write_bytes(content)
    return f"/api/v1/files/{subdir}/{unique_name}"


def resolve_local_path(url_path: str) -> Path | None:
    if not is_local_url(url_path):
        return None
    rel = url_path[len("/api/v1/files/") :]
    full = Path(get_settings().upload_dir) / rel
    return full if full.exists() else None


def read_file_bytes(ref: str) -> bytes:
    local = resolve_local_path(ref)
    if local:
        return local.read_bytes()
    if is_oss_ref(ref):
        key = oss_key_from_ref(ref)
        return _get_bucket().get_object(key).read()
    raise FileNotFoundError(f"无法读取文件: {ref}")


def get_signed_url(ref: str, expires: int = 3600) -> str:
    if not ref:
        return ref
    if is_local_url(ref):
        return ref
    if not is_oss_ref(ref):
        return ref
    s = get_settings()
    if not s.oss_enabled:
        return ref
    key = oss_key_from_ref(ref)
    url = _get_bucket().sign_url("GET", key, expires, slash_safe=True)
    if url.startswith("http://") and s.oss_endpoint.startswith("https"):
        url = "https://" + url[7:]
    return url


def enrich_media_url(url: str | None, expires: int = 3600) -> str | None:
    """返回给前端的可访问地址：本地路径不变，OSS 转为签名 URL。"""
    if not url:
        return None
    if is_oss_ref(url):
        return get_signed_url(url, expires)
    return url


@contextmanager
def open_as_path(ref: str) -> Iterator[tuple[Path, bool]]:
    """解析为本地 Path；OSS 文件会下载到临时文件，用完后自动删除。"""
    local = resolve_local_path(ref)
    if local:
        yield local, False
    elif is_oss_ref(ref):
        key = oss_key_from_ref(ref)
        suffix = Path(key).suffix or ".bin"
        import os

        fd, tmp_name = tempfile.mkstemp(suffix=suffix)
        tmp_path = Path(tmp_name)
        try:
            data = _get_bucket().get_object(key).read()
            os.write(fd, data)
            os.close(fd)
            fd = -1
            yield tmp_path, True
        finally:
            if fd >= 0:
                os.close(fd)
            if tmp_path.exists():
                tmp_path.unlink()
    else:
        raise FileNotFoundError(f"文件不存在: {ref}")


def guess_media_type(ref: str, fallback: str = "application/octet-stream") -> str:
    name = ref.split("/")[-1] if ref else ""
    if name.startswith("oss://"):
        name = name[6:]
    mt, _ = mimetypes.guess_type(name)
    return mt or fallback


def file_inline_response(ref: str, filename: str | None = None):
    from fastapi.responses import FileResponse, Response

    local = resolve_local_path(ref)
    name = filename or Path(oss_key_from_ref(ref) if is_oss_ref(ref) else ref).name
    if local:
        return FileResponse(local, filename=name, media_type=guess_media_type(name))
    data = read_file_bytes(ref)
    return Response(
        content=data,
        media_type=guess_media_type(ref),
        headers={"Content-Disposition": f'inline; filename="{name}"'},
    )


def file_download_response(ref: str, filename: str):
    from fastapi.responses import FileResponse, Response

    local = resolve_local_path(ref)
    if local:
        return FileResponse(local, filename=filename, media_type=guess_media_type(filename))
    data = read_file_bytes(ref)
    return Response(
        content=data,
        media_type=guess_media_type(ref),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

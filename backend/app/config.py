from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _BACKEND_DIR.parent


def _env_file_paths() -> tuple[str, ...]:
    """Load project root .env then backend/.env (later overrides)."""
    paths: list[str] = []
    for p in (_PROJECT_ROOT / ".env", _BACKEND_DIR / ".env"):
        if p.is_file():
            paths.append(str(p))
    return tuple(paths) if paths else (".env",)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_file_paths(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "mysql+pymysql://interview:interview123@localhost:3306/interview_assistant?charset=utf8mb4"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "dev-secret-change-me"
    jwt_expire_minutes: int = 10080

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-pro"

    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    oss_bucket: str = ""
    oss_endpoint: str = ""
    oss_cdn_domain: str = ""

    aliyun_asr_app_key: str = ""
    aliyun_asr_access_key_id: str = ""
    aliyun_asr_access_key_secret: str = ""

    upload_dir: str = "uploads"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def oss_enabled(self) -> bool:
        return bool(
            self.oss_access_key_id
            and self.oss_access_key_secret
            and self.oss_bucket
            and self.oss_endpoint
        )

    @property
    def deepseek_enabled(self) -> bool:
        return bool(self.deepseek_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str = ''
    database_schema: str = 'accident_alert'
    openrouter_api_key: str = ''
    openrouter_model: str = 'openrouter/free'
    jwt_secret: str = ''
    frontend_origins: str = 'http://localhost:5173'
    cookie_secure: bool = False
    data_dir: str = './data'
    yolo_model: str = 'yolo11n.pt'
    ffmpeg_binary: str = 'ffmpeg'
    camera_allowed_hosts: str = ''
    webhook_allowed_hosts: str = ''
    max_upload_mb: int = 100
    auto_alert_candidates: bool = False
    worker_enabled: bool = True

    @property
    def media(self) -> Path:
        path = Path(self.data_dir).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()

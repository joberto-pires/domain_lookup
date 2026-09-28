from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str
    provider_base_url: str = "https://app.agniops.in/v1/search"
    mock_mode: bool = False
    max_attempts: int = 3
    retry_delay_seconds: int = 5
    http_timeout: float = 10.0

settings = Settings()

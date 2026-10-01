from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Tutor"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ai_tutor"
    session_cookie_secure: bool = False
    redis_url: str = "redis://localhost:6379/0"
    parent_unlock_ttl_seconds: int = 600
    parent_pin_max_attempts: int = 5
    parent_pin_window_seconds: int = 300

    ai_provider: str = "fallback"
    openai_model: str = "gpt-5"
    gemini_model: str = "gemini-3.8-flash"
    ai_timeout_seconds: float = 2.5
    llm_gateway_url: str = "http://localhost:8001"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

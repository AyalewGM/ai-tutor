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

    # Fernet key encrypting staff TOTP secrets at rest. Generate with:
    #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    mfa_encryption_key: str | None = None
    admin_mfa_max_attempts: int = 5
    admin_mfa_window_seconds: int = 300

    # Pilot gate: self-registered families wait for admin approval.
    require_family_approval: bool = True
    # Base URL used in email links (no trailing slash).
    public_base_url: str = "http://localhost:3000"

    # Outbound email. "console" logs a redacted summary and sends nothing;
    # "smtp" delivers (Gmail: smtp.gmail.com:587 with an app password).
    email_backend: str = "console"  # console | smtp
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_timeout_seconds: float = 10.0
    email_from: str | None = None
    # Where "new family awaiting approval" notifications go.
    admin_notification_email: str | None = None

    photo_ocr_provider: str = "auto"  # auto | mathpix | stub | disabled
    mathpix_app_id: str | None = None
    mathpix_app_key: str | None = None
    photo_ocr_timeout_seconds: float = 10.0

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

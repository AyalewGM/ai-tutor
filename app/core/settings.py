from decimal import Decimal

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

    # Base URL used in email links (no trailing slash).
    public_base_url: str = "http://localhost:3000"

    # Stripe billing. Empty key = billing disabled (checkout returns 503).
    # Trial requires a card: checkout sets payment_method_collection=always.
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_trial_days: int = 14

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

    # Cloudflare edge protection. Only enable cloudflare_trusted once the
    # origin is locked down so only Cloudflare can reach it — otherwise the
    # CF-* headers are spoofable. geo_enforcement_enabled blocks every
    # request whose country is missing, unknown, or outside allowed_countries
    # (fail closed). Sign-in/config/health stay reachable so approved
    # families can sign in while travelling.
    cloudflare_trusted: bool = False
    geo_enforcement_enabled: bool = False
    allowed_countries: str = "US,CA"

    # Sign-in / registration throttles (Redis-backed, fail closed). Only
    # disable in tests/dev — production must keep this on.
    auth_throttles_enabled: bool = True
    login_rate_limit_per_ip: int = 20
    login_rate_window_seconds: int = 900
    register_rate_limit_per_ip: int = 5
    register_rate_window_seconds: int = 3600
    login_max_failed_attempts: int = 5
    login_lockout_seconds: int = 900

    # Cloudflare Turnstile bot check on sign-in/registration. Enabled when
    # the secret key is set; fail closed in production.
    turnstile_site_key: str | None = None
    turnstile_secret_key: str | None = None
    turnstile_timeout_seconds: float = 5.0

    @property
    def allowed_country_set(self) -> set[str]:
        return {c.strip().upper() for c in self.allowed_countries.split(",") if c.strip()}

    photo_ocr_provider: str = "auto"  # auto | mathpix | stub | disabled
    mathpix_app_id: str | None = None
    mathpix_app_key: str | None = None
    photo_ocr_timeout_seconds: float = 10.0

    ai_provider: str = "fallback"
    openai_model: str = "gpt-5"
    gemini_model: str = "gemini-3.8-flash"
    ai_timeout_seconds: float = 2.5
    llm_gateway_url: str = "http://localhost:8001"
    # AI budgets: per-family daily generation cap (overridable per family via
    # parent_profiles.ai_daily_limit), a global monthly USD cap, and the alert
    # threshold. Denied calls fall back to built-in tutor messages.
    ai_budgets_enabled: bool = True
    family_ai_daily_generations: int = 50
    ai_monthly_cost_cap_usd: Decimal = Decimal("200.00")
    ai_budget_alert_pct: float = 0.8
    # CAD pricing: fallback USD→CAD rate when no Bank of Canada average has
    # been stored yet, and the fetch timeout for the recalc action.
    usd_to_cad_fallback: Decimal = Decimal("1.36")
    fx_fetch_timeout_seconds: float = 10.0
    # Invite-only pilot onboarding: when enabled, /auth/register-parent
    # requires a scoped, single-use parent invitation. Pilot families get
    # time-bounded seat entitlements — never billing.
    pilot_invite_only: bool = False
    pilot_invite_default_seats: int = 3
    pilot_entitlement_days: int = 90
    # Per-child practice-link activation throttle (per client IP).
    practice_link_activate_rate_limit: int = 10
    practice_link_activate_window_seconds: int = 900
    # Per-link cap on top of the per-IP cap: two parties fighting over one
    # shared link should degrade quickly even from different networks.
    practice_link_activate_per_pass_limit: int = 6
    # A learner session counts as "in use" (blocking a second activation of
    # the same link) only if seen within this window. Stale sessions never
    # block re-entry — they are cleaned up on the next activation.
    practice_link_live_session_window_seconds: int = 900

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

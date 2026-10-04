import logging
import smtplib

from app.core.settings import settings
from app.services import email as email_service
from app.services.email import OutboundEmail, family_rejected_email, send_email

MESSAGE = OutboundEmail(to="parent@example.com", subject="Hello", body="Body")


def test_console_backend_delivers_nothing_and_redacts_recipient(monkeypatch, caplog) -> None:
    monkeypatch.setattr(settings, "email_backend", "console")
    monkeypatch.setattr(smtplib, "SMTP", lambda *a, **k: (_ for _ in ()).throw(AssertionError))
    with caplog.at_level(logging.INFO, logger="ai_tutor.email"):
        assert send_email(MESSAGE) is False
    assert "parent@example.com" not in caplog.text


def test_smtp_without_credentials_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(settings, "email_backend", "smtp")
    monkeypatch.setattr(settings, "smtp_username", None)
    monkeypatch.setattr(settings, "smtp_password", None)
    monkeypatch.setattr(email_service.smtplib, "SMTP", lambda *a, **k: (_ for _ in ()).throw(AssertionError))
    assert send_email(MESSAGE) is False


def test_smtp_delivery_failure_is_swallowed(monkeypatch) -> None:
    monkeypatch.setattr(settings, "email_backend", "smtp")
    monkeypatch.setattr(settings, "smtp_username", "sender@example.com")
    monkeypatch.setattr(settings, "smtp_password", "app-password")

    def boom(*_a, **_k):
        raise smtplib.SMTPConnectError(421, "down")

    monkeypatch.setattr(email_service.smtplib, "SMTP", boom)
    assert send_email(MESSAGE) is False


def test_rejection_email_includes_optional_reason() -> None:
    assert "Maryland" in family_rejected_email("p@example.com", None, "Maryland only").body
    assert "Note from our team" not in family_rejected_email("p@example.com", None, None).body

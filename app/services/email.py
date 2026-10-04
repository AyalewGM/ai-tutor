"""Outbound email: one send function, two backends.

- ``console`` (default): logs a redacted summary (subject + recipient domain)
  and delivers nothing — safe for development and CI.
- ``smtp``: STARTTLS + login (Gmail today; info@mihur.com later is a config
  change only).

Sending never raises into request handling: callers schedule it as a
background task, and a failed send is logged, not surfaced to the family.
"""

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage as MimeMessage

from app.core.settings import settings

logger = logging.getLogger("ai_tutor.email")


@dataclass(frozen=True)
class OutboundEmail:
    to: str
    subject: str
    body: str


def _recipient_domain(address: str) -> str:
    return address.rsplit("@", 1)[-1] if "@" in address else "invalid"


def send_email(message: OutboundEmail) -> bool:
    backend = settings.email_backend.strip().lower()
    summary = {"subject": message.subject, "to_domain": _recipient_domain(message.to)}
    if backend != "smtp":
        logger.info("email (console backend, not delivered)", extra=summary)
        return False
    sender = settings.email_from or settings.smtp_username
    if not (sender and settings.smtp_username and settings.smtp_password):
        logger.error("email not sent: SMTP credentials are not configured", extra=summary)
        return False
    mime = MimeMessage()
    mime["From"] = f"Mihur <{sender}>"
    mime["To"] = message.to
    mime["Subject"] = message.subject
    mime.set_content(message.body)
    try:
        with smtplib.SMTP(
            settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds
        ) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(mime)
    except (smtplib.SMTPException, OSError):
        logger.exception("email delivery failed", extra=summary)
        return False
    logger.info("email sent", extra=summary)
    return True


def new_family_notification(parent_email: str, display_name: str | None) -> OutboundEmail | None:
    if not settings.admin_notification_email:
        return None
    who = f"{display_name} <{parent_email}>" if display_name else parent_email
    return OutboundEmail(
        to=settings.admin_notification_email,
        subject="New Mihur family awaiting approval",
        body=(
            f"A new family has registered and is waiting for approval:\n\n"
            f"  {who}\n\n"
            f"Review it in the admin dashboard: {settings.public_base_url}/admin\n"
        ),
    )


def family_approved_email(parent_email: str, display_name: str | None) -> OutboundEmail:
    greeting = f"Hi {display_name}," if display_name else "Hello,"
    return OutboundEmail(
        to=parent_email,
        subject="Your Mihur account is approved",
        body=(
            f"{greeting}\n\n"
            "Good news: your family's Mihur account has been approved for the pilot.\n"
            f"Sign in to add your learner and start practicing: {settings.public_base_url}/login\n\n"
            "Thank you for helping us build Mihur.\n— The Mihur team\n"
        ),
    )


def family_rejected_email(
    parent_email: str, display_name: str | None, reason: str | None
) -> OutboundEmail:
    greeting = f"Hi {display_name}," if display_name else "Hello,"
    reason_line = f"\nNote from our team: {reason}\n" if reason else ""
    return OutboundEmail(
        to=parent_email,
        subject="An update on your Mihur pilot request",
        body=(
            f"{greeting}\n\n"
            "Thank you for your interest in Mihur. We're not able to include your "
            "family in the current pilot.\n"
            f"{reason_line}\n"
            "We'll be in touch as Mihur opens to more families.\n— The Mihur team\n"
        ),
    )

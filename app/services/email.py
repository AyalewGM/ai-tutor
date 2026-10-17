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
        subject="New Mihur family registered",
        body=(
            f"A new family has registered:\n\n"
            f"  {who}\n\n"
            f"See it in the admin dashboard: {settings.public_base_url}/admin\n"
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


def family_welcome_email(
    parent_email: str, display_name: str | None, region_name: str | None
) -> OutboundEmail:
    greeting = f"Hi {display_name}," if display_name else "Hello,"
    region_line = (
        f"Your family's region is set to {region_name}, so your learners will "
        "see the matching curriculum.\n"
        if region_name
        else ""
    )
    return OutboundEmail(
        to=parent_email,
        subject="Welcome to the Mihur pilot",
        body=(
            f"{greeting}\n\n"
            "Your Mihur family account is ready.\n\n"
            f"{region_line}"
            "Next steps:\n"
            "1. Sign in and add each of your children as a learner.\n"
            "2. From the family dashboard, generate a private practice link "
            "for each child — one link per child.\n"
            "3. Share each link only with that child. A link works on one "
            "device at a time.\n\n"
            f"Sign in here: {settings.public_base_url}/login\n\n"
            "Thank you for helping us build Mihur.\n— The Mihur team\n"
        ),
    )


def family_invitation_email(to_email: str, token: str, seats: int | None) -> OutboundEmail:
    seat_line = (
        f"This invitation covers up to {seats} learners.\n" if seats else ""
    )
    return OutboundEmail(
        to=to_email,
        subject="Your Mihur pilot invitation",
        body=(
            "Hello,\n\n"
            "You've been invited to the Mihur pilot.\n\n"
            f"{seat_line}"
            "Register your family here (one-time use):\n"
            f"{settings.public_base_url}/login#invite={token}\n\n"
            "This link is for your family only — please don't share it.\n\n"
            "— The Mihur team\n"
        ),
    )

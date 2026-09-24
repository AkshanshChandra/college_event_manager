import logging
import smtplib
from abc import ABC, abstractmethod
from email.message import EmailMessage

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("adappt.email")


class EmailBackend(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, html_body: str, text_body: str) -> None: ...


class ConsoleEmailBackend(EmailBackend):
    """Dev backend: logs the email instead of sending it, so the activation /
    credential-delivery flow can be exercised locally with no provider signup.
    """

    def send(self, to: str, subject: str, html_body: str, text_body: str) -> None:
        logger.info(
            "\n----- EMAIL (console backend) -----\nTo: %s\nSubject: %s\n\n%s\n------------------------------------",
            to,
            subject,
            text_body,
        )


class SMTPEmailBackend(EmailBackend):
    def send(self, to: str, subject: str, html_body: str, text_body: str) -> None:
        message = EmailMessage()
        message["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>"
        message["To"] = to
        message["Subject"] = subject
        message.set_content(text_body)
        message.add_alternative(html_body, subtype="html")

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)


_email_instance: EmailBackend | None = None


def get_email_backend() -> EmailBackend:
    global _email_instance
    if _email_instance is not None:
        return _email_instance
    if settings.EMAIL_BACKEND == "smtp":
        _email_instance = SMTPEmailBackend()
    else:
        _email_instance = ConsoleEmailBackend()
    return _email_instance


def send_activation_email(to: str, team_name: str, activation_url: str) -> None:
    subject = "Activate your ADAPPT portal account"
    text_body = (
        f"Hi,\n\nYour team \"{team_name}\" is registered for ADAPPT.\n\n"
        f"Activate your portal account and set a password here:\n{activation_url}\n\n"
        f"This link expires in {settings.ACTIVATION_TOKEN_EXPIRE_HOURS} hours.\n\n"
        f"— ADAPPT Organizing Committee"
    )
    html_body = f"""
    <div style="font-family: sans-serif; max-width: 480px;">
      <h2>Activate your ADAPPT portal account</h2>
      <p>Your team <strong>{team_name}</strong> is registered for ADAPPT.</p>
      <p><a href="{activation_url}" style="background:#111827;color:#fff;padding:10px 20px;
        border-radius:6px;text-decoration:none;">Activate account</a></p>
      <p style="color:#6b7280;font-size:13px;">This link expires in
        {settings.ACTIVATION_TOKEN_EXPIRE_HOURS} hours.</p>
    </div>
    """
    get_email_backend().send(to, subject, html_body, text_body)


def send_submission_confirmation_email(to: str, team_name: str, submitted_at: str) -> None:
    subject = "ADAPPT Round 1 submission received"
    text_body = (
        f"Hi,\n\nWe received Round 1 submission for team \"{team_name}\" at {submitted_at} UTC.\n\n"
        f"— ADAPPT Organizing Committee"
    )
    html_body = f"""
    <div style="font-family: sans-serif; max-width: 480px;">
      <h2>Submission received</h2>
      <p>We received the Round 1 submission for <strong>{team_name}</strong> at {submitted_at} UTC.</p>
    </div>
    """
    get_email_backend().send(to, subject, html_body, text_body)

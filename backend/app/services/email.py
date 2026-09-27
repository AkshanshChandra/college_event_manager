import logging
import smtplib
from abc import ABC, abstractmethod
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

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


class ResendEmailBackend(EmailBackend):
    """Transactional email via Resend's API (https://resend.com).

    Recommended over raw Gmail SMTP for production: Resend lets you verify
    your own sending domain (SPF/DKIM/DMARC), so mail is sent as
    noreply@adappt.ietempstme.com instead of a personal Gmail address — the
    single biggest lever for landing in the inbox instead of spam, since the
    sender domain then matches the links in the email.
    """

    def __init__(self) -> None:
        import resend

        resend.api_key = settings.RESEND_API_KEY
        self._resend = resend

    def send(self, to: str, subject: str, html_body: str, text_body: str) -> None:
        self._resend.Emails.send(
            {
                "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>",
                "to": [to],
                "reply_to": settings.EMAIL_FROM_ADDRESS,
                "subject": subject,
                "html": html_body,
                "text": text_body,
            }
        )


class SMTPEmailBackend(EmailBackend):
    def send(self, to: str, subject: str, html_body: str, text_body: str) -> None:
        message = EmailMessage()
        message["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>"
        message["To"] = to
        message["Reply-To"] = settings.EMAIL_FROM_ADDRESS
        message["Subject"] = subject
        # Missing Date/Message-ID headers are a common, easy-to-fix spam
        # signal — mail clients and spam filters expect both on legitimate
        # mail, and Python's smtplib doesn't add them automatically.
        message["Date"] = formatdate(localtime=True)
        message["Message-ID"] = make_msgid(domain=settings.EMAIL_FROM_ADDRESS.split("@")[-1])
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
    if settings.EMAIL_BACKEND == "resend":
        _email_instance = ResendEmailBackend()
    elif settings.EMAIL_BACKEND == "smtp":
        _email_instance = SMTPEmailBackend()
    else:
        _email_instance = ConsoleEmailBackend()
    return _email_instance


_FOOTER_TEXT = (
    "\n\n---\nADAPPT 5.0 · Organized by IETE Student Forum, MPSTME\n"
    "https://adappt.ietempstme.com\n"
    "You're receiving this because this email address registered a team for ADAPPT 5.0. "
    "If that wasn't you, you can safely ignore this message."
)

_FOOTER_HTML = """
    <p style="margin-top:24px;padding-top:16px;border-top:1px solid #e5e7eb;
      color:#6b7280;font-size:12px;line-height:1.6;">
      ADAPPT 5.0 · Organized by IETE Student Forum, MPSTME<br>
      <a href="https://adappt.ietempstme.com" style="color:#6b7280;">adappt.ietempstme.com</a><br>
      You're receiving this because this email address registered a team for ADAPPT 5.0.
      If that wasn't you, you can safely ignore this message.
    </p>
"""


def _logo_header_html() -> str:
    logo_url = f"{settings.FRONTEND_URL}/committee-logo.png"
    return f"""
    <div style="text-align:center;margin-bottom:16px;">
      <img src="{logo_url}" alt="IETE Student Forum, MPSTME" width="56" height="56"
        style="border-radius:50%;display:inline-block;">
    </div>
    """


def send_activation_email(to: str, team_name: str, activation_url: str) -> None:
    subject = "Activate your ADAPPT portal account"
    text_body = (
        f"Hi,\n\nYour team \"{team_name}\" is registered for ADAPPT 5.0.\n\n"
        f"Activate your portal account and set a password here:\n{activation_url}\n\n"
        f"This link expires in {settings.ACTIVATION_TOKEN_EXPIRE_HOURS} hours.\n\n"
        f"— ADAPPT Organizing Committee" + _FOOTER_TEXT
    )
    html_body = f"""
    <div style="font-family: sans-serif; max-width: 480px; color:#111827;">
      {_logo_header_html()}
      <h2>Activate your ADAPPT portal account</h2>
      <p>Your team <strong>{team_name}</strong> is registered for ADAPPT 5.0.</p>
      <p><a href="{activation_url}" style="background:#c92c37;color:#fff;padding:10px 20px;
        border-radius:6px;text-decoration:none;display:inline-block;">Activate account</a></p>
      <p style="color:#6b7280;font-size:13px;">This link expires in
        {settings.ACTIVATION_TOKEN_EXPIRE_HOURS} hours.</p>
      {_FOOTER_HTML}
    </div>
    """
    get_email_backend().send(to, subject, html_body, text_body)


def send_submission_confirmation_email(to: str, team_name: str, submitted_at: str) -> None:
    subject = "ADAPPT Round 1 submission received"
    text_body = (
        f"Hi,\n\nWe received Round 1 submission for team \"{team_name}\" at {submitted_at} UTC.\n\n"
        f"— ADAPPT Organizing Committee" + _FOOTER_TEXT
    )
    html_body = f"""
    <div style="font-family: sans-serif; max-width: 480px; color:#111827;">
      {_logo_header_html()}
      <h2>Submission received</h2>
      <p>We received the Round 1 submission for <strong>{team_name}</strong> at {submitted_at} UTC.</p>
      {_FOOTER_HTML}
    </div>
    """
    get_email_backend().send(to, subject, html_body, text_body)

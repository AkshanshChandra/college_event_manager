import base64
import logging
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("adappt.email")


@dataclass
class EmailAttachment:
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


class EmailBackend(ABC):
    @abstractmethod
    def send(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: str,
        attachments: list[EmailAttachment] | None = None,
    ) -> None: ...


class ConsoleEmailBackend(EmailBackend):
    """Dev backend: logs the email instead of sending it, so the activation /
    credential-delivery flow can be exercised locally with no provider signup.
    """

    def send(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: str,
        attachments: list[EmailAttachment] | None = None,
    ) -> None:
        attachment_note = (
            f"\nAttachments: {', '.join(a.filename for a in attachments)}" if attachments else ""
        )
        logger.info(
            "\n----- EMAIL (console backend) -----\nTo: %s\nSubject: %s\n\n%s%s\n------------------------------------",
            to,
            subject,
            text_body,
            attachment_note,
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

    def send(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: str,
        attachments: list[EmailAttachment] | None = None,
    ) -> None:
        payload = {
            "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>",
            "to": [to],
            "reply_to": settings.EMAIL_FROM_ADDRESS,
            "subject": subject,
            "html": html_body,
            "text": text_body,
        }
        if attachments:
            payload["attachments"] = [
                {"filename": a.filename, "content": base64.b64encode(a.content).decode("ascii")}
                for a in attachments
            ]
        self._resend.Emails.send(payload)


class SMTPEmailBackend(EmailBackend):
    def send(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: str,
        attachments: list[EmailAttachment] | None = None,
    ) -> None:
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
        for a in attachments or []:
            maintype, _, subtype = a.content_type.partition("/")
            message.add_attachment(
                a.content, maintype=maintype or "application", subtype=subtype or "octet-stream", filename=a.filename
            )

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


_WHATSAPP_GROUP_URL = "https://chat.whatsapp.com/LRCo4goT4Gz7Ci0h3sxcCq"


def send_activation_email(to: str, team_name: str, activation_url: str) -> None:
    subject = "Activate your ADAPPT portal account"
    text_body = (
        f"Hi,\n\nYour team \"{team_name}\" is registered for ADAPPT 5.0.\n\n"
        f"Activate your portal account and set a password here:\n{activation_url}\n\n"
        f"This link expires in {settings.ACTIVATION_TOKEN_EXPIRE_HOURS} hours.\n\n"
        f"Join the ADAPPT 5.0 WhatsApp group for updates and announcements:\n{_WHATSAPP_GROUP_URL}\n\n"
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
      <p>Join the ADAPPT 5.0 WhatsApp group for updates and announcements:<br>
        <a href="{_WHATSAPP_GROUP_URL}" style="color:#25D366;font-weight:600;">{_WHATSAPP_GROUP_URL}</a></p>
      {_FOOTER_HTML}
    </div>
    """
    get_email_backend().send(to, subject, html_body, text_body)


_ORGANIZER_CONTACTS = [
    ("Akshansh Chandra", "+918586876378"),
    ("Arushi Dube", "+919137086087"),
    ("Arnab Mukhopadhyay", "+918104530548"),
]


def send_round1_reminder_email(to: str, leader_name: str, team_name: str, deadline_text: str) -> None:
    subject = f"ADAPPT 5.0 — Round 1 Submission Deadline: {deadline_text}"
    contacts_text = "\n".join(f"- {name} — {phone}" for name, phone in _ORGANIZER_CONTACTS)
    contacts_html = "".join(
        f'<li style="margin-bottom:4px;">{name} — {phone}</li>' for name, phone in _ORGANIZER_CONTACTS
    )
    text_body = (
        f"Hi {leader_name},\n\n"
        f"This is a reminder that Round 1 submissions for ADAPPT 5.0 are due on {deadline_text}. "
        f"Our records show Team \"{team_name}\" hasn't submitted yet.\n\n"
        f"Please upload your Round 1 submission (a demo video is required; a PPT/PDF is optional) "
        f"through the participant portal before the deadline:\n"
        f"https://adappt.ietempstme.com/submission\n\n"
        f"Submissions will not be accepted after the deadline, so please don't wait until the last minute.\n\n"
        f"If you run into any issues or have questions, reach out to:\n{contacts_text}\n\n"
        f"If you've already submitted and are seeing this by mistake, you can safely ignore this email.\n\n"
        f"— ADAPPT Organizing Committee" + _FOOTER_TEXT
    )
    html_body = f"""
    <div style="font-family: sans-serif; max-width: 480px; color:#111827;">
      {_logo_header_html()}
      <h2>Round 1 Submission Deadline: {deadline_text}</h2>
      <p>Hi {leader_name},</p>
      <p>This is a reminder that Round 1 submissions for ADAPPT 5.0 are due on
        <strong>{deadline_text}</strong>. Our records show Team <strong>{team_name}</strong>
        hasn't submitted yet.</p>
      <p>Please upload your Round 1 submission (a demo video is required; a PPT/PDF is optional)
        through the participant portal before the deadline:</p>
      <p><a href="https://adappt.ietempstme.com/submission" style="background:#c92c37;color:#fff;
        padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block;">
        Submit Round 1</a></p>
      <p style="color:#6b7280;font-size:13px;">Submissions will not be accepted after the
        deadline, so please don't wait until the last minute.</p>
      <p>If you run into any issues or have questions, reach out to:</p>
      <ul style="padding-left:18px;color:#111827;">{contacts_html}</ul>
      <p style="color:#6b7280;font-size:13px;">If you've already submitted and are seeing this
        by mistake, you can safely ignore this email.</p>
      {_FOOTER_HTML}
    </div>
    """
    get_email_backend().send(to, subject, html_body, text_body)


def send_round2_selection_email(
    to: str,
    venue: str,
    reporting_time_text: str,
    event_dates_text: str,
    consent_form_url: str,
    undertaking_attachment: EmailAttachment,
) -> None:
    subject = "ADAPPT 5.0 — You're Selected for Round 2 (Tech Twists)!"
    contacts_text = "\n".join(f"- {name} — {phone}" for name, phone in _ORGANIZER_CONTACTS)
    contacts_html = "".join(
        f'<li style="margin-bottom:4px;">{name} — {phone}</li>' for name, phone in _ORGANIZER_CONTACTS
    )
    text_body = (
        f"Hi,\n\n"
        f"Congratulations! Your team has been selected for Round 2 — Tech Twists of ADAPPT 5.0.\n\n"
        f"Round 2 Details\n"
        f"- Venue: {venue}\n"
        f"- Reporting Time: {reporting_time_text}\n"
        f"- Event Duration: {event_dates_text}\n\n"
        f"Before you arrive, please complete the following:\n\n"
        f"1. Consent Form (required): Fill out this form before the event —\n{consent_form_url}\n\n"
        f"2. Undertaking Letter (attached): Since the event involves an overnight stay on campus, "
        f"please print the attached undertaking letter, get it signed by both the student and a "
        f"parent/guardian, and bring the signed physical copy with you.\n\n"
        f"If you have any questions or need help, reach out to:\n{contacts_text}\n\n"
        f"We're looking forward to seeing you there!\n\n"
        f"— ADAPPT Organizing Committee" + _FOOTER_TEXT
    )
    html_body = f"""
    <div style="font-family: sans-serif; max-width: 480px; color:#111827;">
      {_logo_header_html()}
      <h2>You're Selected for Round 2 — Tech Twists!</h2>
      <p>Congratulations! Your team has been selected for Round 2 of ADAPPT 5.0.</p>
      <p><strong>Round 2 Details</strong></p>
      <ul style="padding-left:18px;">
        <li><strong>Venue:</strong> {venue}</li>
        <li><strong>Reporting Time:</strong> {reporting_time_text}</li>
        <li><strong>Event Duration:</strong> {event_dates_text}</li>
      </ul>
      <p><strong>Before you arrive, please complete the following:</strong></p>
      <ol style="padding-left:18px;">
        <li style="margin-bottom:8px;">
          <strong>Consent Form (required):</strong>
          <a href="{consent_form_url}" style="color:#c92c37;">Fill it out here</a> before the event.
        </li>
        <li>
          <strong>Undertaking Letter (attached):</strong> Since the event involves an overnight stay
          on campus, please print the attached undertaking letter, get it signed by both the student
          and a parent/guardian, and bring the signed physical copy with you.
        </li>
      </ol>
      <p>If you have any questions or need help, reach out to:</p>
      <ul style="padding-left:18px;color:#111827;">{contacts_html}</ul>
      <p>We're looking forward to seeing you there!</p>
      {_FOOTER_HTML}
    </div>
    """
    get_email_backend().send(to, subject, html_body, text_body, attachments=[undertaking_attachment])


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

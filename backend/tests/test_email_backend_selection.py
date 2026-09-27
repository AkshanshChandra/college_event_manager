import app.services.email as email_module
from app.config import get_settings


def _select_backend(monkeypatch, **env):
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    monkeypatch.setattr(email_module, "settings", get_settings())
    monkeypatch.setattr(email_module, "_email_instance", None)
    return email_module.get_email_backend()


def test_console_is_default(monkeypatch):
    backend = _select_backend(monkeypatch, EMAIL_BACKEND="console")
    assert isinstance(backend, email_module.ConsoleEmailBackend)


def test_smtp_backend_selected(monkeypatch):
    backend = _select_backend(monkeypatch, EMAIL_BACKEND="smtp")
    assert isinstance(backend, email_module.SMTPEmailBackend)


def test_resend_backend_selected(monkeypatch):
    backend = _select_backend(monkeypatch, EMAIL_BACKEND="resend", RESEND_API_KEY="re_test_key")
    assert isinstance(backend, email_module.ResendEmailBackend)
    assert backend._resend.api_key == "re_test_key"

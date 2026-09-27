import pytest

from app.config.settings import Settings, assert_production_safety


def _prod_settings(**overrides):
    base = dict(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="a-real-random-secret-key",
        DEBUG=False,
        STORAGE_BACKEND="s3",
        S3_BUCKET_NAME="adappt-uploads",
        EMAIL_BACKEND="smtp",
        SMTP_HOST="smtp.example.com",
    )
    base.update(overrides)
    return Settings(**base)


def test_safe_production_config_boots_cleanly():
    assert_production_safety(_prod_settings())


def test_dev_jwt_secret_blocks_production_boot():
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        assert_production_safety(_prod_settings(JWT_SECRET_KEY="dev-secret-change-me"))


def test_debug_true_blocks_production_boot():
    with pytest.raises(RuntimeError, match="DEBUG"):
        assert_production_safety(_prod_settings(DEBUG=True))


def test_local_storage_blocks_production_boot():
    with pytest.raises(RuntimeError, match="STORAGE_BACKEND"):
        assert_production_safety(_prod_settings(STORAGE_BACKEND="local"))


def test_console_email_blocks_production_boot():
    with pytest.raises(RuntimeError, match="EMAIL_BACKEND"):
        assert_production_safety(_prod_settings(EMAIL_BACKEND="console"))


def test_development_environment_is_never_checked():
    # Any of the "unsafe" values are fine outside production.
    assert_production_safety(Settings(ENVIRONMENT="development"))
    assert_production_safety(Settings(ENVIRONMENT="test"))

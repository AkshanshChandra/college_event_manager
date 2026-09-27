from app.services.storage import build_content_disposition

# macOS Screenshot app uses U+202F (narrow no-break space) between the time
# and AM/PM, e.g. "10.51.09 PM" — this is exactly what broke S3's
# response-content-disposition parameter in production (it must be
# ISO-8859-1, and U+202F isn't representable in that charset).
MACOS_SCREENSHOT_FILENAME = "Screenshot 2026-09-27 at 10.51.09 PM.png"


def test_content_disposition_is_iso_8859_1_safe_for_macos_screenshot_names():
    header_value = build_content_disposition(MACOS_SCREENSHOT_FILENAME)
    # This is the exact check S3 (and any spec-compliant HTTP layer) applies —
    # if this doesn't raise, the header is safe to send.
    header_value.encode("iso-8859-1")


def test_content_disposition_ascii_fallback_strips_bad_characters():
    header_value = build_content_disposition(MACOS_SCREENSHOT_FILENAME)
    assert 'filename="Screenshot 2026-09-27 at 10.51.09PM.png"' in header_value


def test_content_disposition_includes_rfc5987_encoded_exact_name():
    header_value = build_content_disposition(MACOS_SCREENSHOT_FILENAME)
    assert "filename*=UTF-8''Screenshot%202026-09-27%20at%2010.51.09%E2%80%AFPM.png" in header_value


def test_content_disposition_plain_ascii_filename_unaffected():
    header_value = build_content_disposition("payment_proof.png")
    assert header_value == "attachment; filename=\"payment_proof.png\"; filename*=UTF-8''payment_proof.png"
    header_value.encode("iso-8859-1")


def test_content_disposition_handles_filename_that_is_entirely_non_ascii():
    # Non-ASCII characters are dropped from the fallback, not left empty —
    # ".png" survives here since only the two U+202F chars are stripped.
    header_value = build_content_disposition("  .png")
    header_value.encode("iso-8859-1")
    assert 'filename=".png"' in header_value

    # An entirely-unrepresentable filename still falls back to something.
    header_value = build_content_disposition("  ")
    header_value.encode("iso-8859-1")
    assert 'filename="download"' in header_value

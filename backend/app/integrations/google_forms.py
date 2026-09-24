"""Google Sheets integration for syncing Google Form registration responses.

This module talks to the Google Sheets API only — it knows nothing about our
database or participant auth (that lives in app.services.registration_sync).
Requires GOOGLE_SERVICE_ACCOUNT_JSON (path to a service account key file with
read access to the response spreadsheet) and GOOGLE_SHEET_ID to be set.
"""

from app.config import get_settings

settings = get_settings()

REQUIRED_ENV_VARS = ("GOOGLE_SERVICE_ACCOUNT_JSON", "GOOGLE_SHEET_ID")


class GoogleSheetsNotConfigured(RuntimeError):
    pass


def fetch_registration_rows() -> list[dict]:
    """Returns the response sheet as a list of {column_header: value} dicts,
    exactly as gspread's get_all_records() shapes it.
    """
    if not settings.GOOGLE_SERVICE_ACCOUNT_JSON or not settings.GOOGLE_SHEET_ID:
        raise GoogleSheetsNotConfigured(
            "Set GOOGLE_SERVICE_ACCOUNT_JSON and GOOGLE_SHEET_ID to sync from Google Sheets. "
            "Until then, use REGISTRATION_SYNC_MODE=csv for local development."
        )

    import gspread
    from google.oauth2.service_account import Credentials

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    credentials = Credentials.from_service_account_file(
        settings.GOOGLE_SERVICE_ACCOUNT_JSON, scopes=scopes
    )
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(settings.GOOGLE_SHEET_ID)
    worksheet = sheet.worksheet(settings.GOOGLE_SHEET_WORKSHEET)
    return worksheet.get_all_records()

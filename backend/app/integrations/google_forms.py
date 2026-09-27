"""Google Sheets integration.

This module talks to the Google Sheets API only — it knows nothing about our
database or participant auth (that lives in app.services.registration_sync).
Requires GOOGLE_SERVICE_ACCOUNT_JSON (path to a service account key file
shared with edit access on the target spreadsheet) and GOOGLE_SHEET_ID.

Two directions are supported:
  - push_rows_to_sheet: the portal's own registration form is the source of
    truth, so registrations are pushed OUT to a sheet for organizers who want
    to view/filter/share the list in a familiar spreadsheet.
  - fetch_registration_rows: reads a sheet's rows IN, for the optional
    legacy bulk-import path (e.g. importing an existing spreadsheet of
    registrations collected before the native form existed).
"""

from app.config import get_settings

settings = get_settings()


class GoogleSheetsNotConfigured(RuntimeError):
    pass


def _open_worksheet(scopes: list[str]):
    if not settings.GOOGLE_SERVICE_ACCOUNT_JSON or not settings.GOOGLE_SHEET_ID:
        raise GoogleSheetsNotConfigured(
            "Set GOOGLE_SERVICE_ACCOUNT_JSON and GOOGLE_SHEET_ID to use Google Sheets sync."
        )

    import gspread
    from google.oauth2.service_account import Credentials

    credentials = Credentials.from_service_account_file(
        settings.GOOGLE_SERVICE_ACCOUNT_JSON, scopes=scopes
    )
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(settings.GOOGLE_SHEET_ID)
    try:
        return sheet.worksheet(settings.GOOGLE_SHEET_WORKSHEET)
    except gspread.WorksheetNotFound:
        return sheet.add_worksheet(title=settings.GOOGLE_SHEET_WORKSHEET, rows=1000, cols=20)


def fetch_registration_rows() -> list[dict]:
    """Returns the sheet as a list of {column_header: value} dicts, for the
    optional legacy bulk-import path.
    """
    worksheet = _open_worksheet(["https://www.googleapis.com/auth/spreadsheets.readonly"])
    return worksheet.get_all_records()


def push_rows_to_sheet(headers: list[str], rows: list[list]) -> None:
    """Overwrites the configured worksheet with a fresh header + data rows.

    This is a full resync (not an append) so the sheet always mirrors the
    portal's registrations table exactly, with no drift or duplicate rows.
    """
    worksheet = _open_worksheet(["https://www.googleapis.com/auth/spreadsheets"])
    worksheet.clear()
    worksheet.update([headers, *rows], value_input_option="USER_ENTERED")

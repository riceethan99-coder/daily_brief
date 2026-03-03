import json
import os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from googleapiclient.discovery import build

TIMEZONE = ZoneInfo("Europe/London")


def get_calendar_events() -> list[str]:
    """
    Fetch today's events from Google Calendar and return a list of
    formatted strings like "09:00 — Team standup" or "All day — Bank Holiday".
    """
    creds_json = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    credentials = service_account.Credentials.from_service_account_info(
        creds_json,
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
    )

    service = build("calendar", "v3", credentials=credentials, cache_discovery=False)

    # Today's window in UTC
    now_local = datetime.now(TIMEZONE)
    start = now_local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    end = start + timedelta(days=1)

    result = service.events().list(
        calendarId=os.environ["GOOGLE_CALENDAR_ID"],
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = []
    for item in result.get("items", []):
        events.append(_format_event(item))

    return events


def _format_event(event: dict) -> str:
    start = event["start"]
    end = event["end"]
    summary = event.get("summary", "(No title)")

    if "dateTime" in start:
        start_dt = datetime.fromisoformat(start["dateTime"]).astimezone(TIMEZONE)
        end_dt = datetime.fromisoformat(end["dateTime"]).astimezone(TIMEZONE)
        return f"{start_dt.strftime('%H:%M')}–{end_dt.strftime('%H:%M')} — {summary}"
    else:
        # All-day event
        return f"All day — {summary}"

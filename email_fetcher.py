import os
from email.utils import parseaddr

import anthropic
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def get_emails() -> list[str]:
    """
    Fetch unread emails from the Primary inbox in the last 24 hours, filter
    them through Claude AI, and return formatted "Name — summary" strings.

    Returns an empty list if anything fails so the rest of the brief still sends.
    """
    try:
        return _fetch_and_filter_emails()
    except Exception as e:
        print(f"[email_fetcher] Error: {e}")
        return []


def _fetch_and_filter_emails() -> list[str]:
    credentials = Credentials(
        token=None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )

    service = build("gmail", "v1", credentials=credentials, cache_discovery=False)

    # category:primary limits to the Primary tab only — excludes Promotions,
    # Social, Updates, Forums, Spam, and Trash
    result = service.users().messages().list(
        userId="me",
        q="is:unread newer_than:1d category:primary",
        maxResults=50,
    ).execute()

    messages = result.get("messages", [])
    if not messages:
        return []

    email_metadata = []
    for msg in messages:
        detail = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["From"],
        ).execute()

        headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
        raw_from = headers.get("From", "")

        # parseaddr turns "Alice Smith <alice@example.com>" into ("Alice Smith", "alice@example.com")
        # Falls back to the raw email address if there's no display name
        display_name, address = parseaddr(raw_from)
        sender_name = display_name if display_name else address

        # snippet is a short plain-text preview Google generates — no need to fetch the body
        snippet = detail.get("snippet", "")

        email_metadata.append({"name": sender_name, "snippet": snippet})

    return _filter_with_claude(email_metadata)


def _filter_with_claude(emails: list[dict]) -> list[str]:
    email_lines = "\n".join(
        f"{i + 1}. From: {e['name']} | Preview: {e['snippet']}"
        for i, e in enumerate(emails)
    )

    prompt = f"""You are filtering emails for a person's daily brief.

Here are unread emails from their Primary inbox in the last 24 hours:

{email_lines}

Identify only the emails that genuinely need the person's attention today.

EXCLUDE:
- Newsletters and subscription emails
- Automated notifications (GitHub, Jira, monitoring, CI/CD, etc.)
- Marketing and promotional emails
- Order confirmations, receipts, and shipping updates
- Social media notifications
- Weekly/daily digest emails from any service

INCLUDE:
- Emails from real people that appear to need a reply or action
- Important account or security alerts
- Calendar invitations or meeting requests
- Anything time-sensitive or urgent

For each email that needs attention, return one line using this exact format:
- <sender name> — <one short sentence summarising what they want or need>

Example: - Alice — Asking if you can join the 3pm meeting on Thursday

If no emails need attention, return exactly: NONE"""

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()

    if raw == "NONE":
        return []

    result = []
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("- "):
            result.append(line[2:])

    return result

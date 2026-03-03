from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from notion_manager import get_tasks
from calendar_fetcher import get_calendar_events
from email_fetcher import get_emails
from focus_generator import get_focus
from telegram_sender import send_message


def format_brief(
    recurring: list[str],
    todos: list[str],
    events: list[str],
    emails: list[str],
    focus: str,
) -> str:
    now = datetime.now()
    today = now.strftime(f"%A, {now.day} %B")  # e.g. "Monday, 2 March"

    lines = [f"Good morning! Here's your brief for {today}\n"]

    # --- Focus for Today (top of brief) ---
    if focus:
        lines.append("🎯 *FOCUS FOR TODAY*")
        lines.append(focus)
        lines.append("")

    # --- Calendar section ---
    if events:
        lines.append("📅 *TODAY'S CALENDAR*")
        for event in events:
            lines.append(f"• {event}")
    else:
        lines.append("📅 *TODAY'S CALENDAR* — nothing scheduled")

    # --- Today's tasks section ---
    lines.append("")
    if todos:
        lines.append("📋 *TODAY'S TASKS*")
        for task in todos:
            lines.append(f"• {task}")
    else:
        lines.append("📋 *TODAY'S TASKS* — nothing on the list")

    # --- Recurring habits section ---
    lines.append("")
    if recurring:
        lines.append("↺ *RECURRING*")
        for habit in recurring:
            lines.append(f"• {habit}")
    else:
        lines.append("↺ *RECURRING* — no habits configured")

    # --- Email section ---
    lines.append("")
    if emails:
        lines.append("📧 *EMAILS*")
        for email in emails:
            lines.append(f"• {email}")
    else:
        lines.append("📧 *EMAILS* — inbox clear")

    # --- Placeholder for future sections ---
    lines.append("\n💼 *LinkedIn* — coming soon")

    return "\n".join(lines)


def main():
    load_dotenv(Path(__file__).parent / ".env")  # no-op in GitHub Actions (env vars already set)

    recurring, todos = get_tasks()
    events = get_calendar_events()
    emails = get_emails()
    focus = get_focus(events, todos, recurring, emails)
    message = format_brief(recurring, todos, events, emails, focus)
    send_message(message)
    print("Brief sent successfully.")


if __name__ == "__main__":
    main()

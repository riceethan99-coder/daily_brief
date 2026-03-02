from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from notion_fetcher import get_todos
from telegram_sender import send_message


def format_brief(todos: list[str]) -> str:
    now = datetime.now()
    today = now.strftime(f"%A, {now.day} %B")  # e.g. "Monday, 2 March"

    lines = [f"Good morning! Here's your brief for {today}\n"]

    # --- To-do section ---
    if todos:
        lines.append(f"📋 *TO-DO* ({len(todos)} item{'s' if len(todos) != 1 else ''})")
        for task in todos:
            lines.append(f"• {task}")
    else:
        lines.append("📋 *TO-DO* — nothing on the list today!")

    # --- Placeholder for future sections ---
    lines.append("\n💼 *LinkedIn* — coming soon")

    return "\n".join(lines)


def main():
    load_dotenv(Path(__file__).parent / ".env")  # no-op in GitHub Actions (env vars already set)

    todos = get_todos()
    message = format_brief(todos)
    send_message(message)
    print("Brief sent successfully.")


if __name__ == "__main__":
    main()

import os
import requests


def send_message(text: str) -> None:
    """Send a Markdown-formatted message to your Telegram chat."""
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }

    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()

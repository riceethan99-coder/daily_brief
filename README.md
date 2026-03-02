# Daily Brief

A Python script that sends a daily morning Telegram message with your Notion to-dos. Runs automatically via GitHub Actions — no server required.

## What it sends

- **To-do list** — unchecked to-do items from a Notion page
- *LinkedIn integration coming soon*

## Setup

### 1. Telegram bot

1. Message `@BotFather` on Telegram → `/newbot` → follow the prompts
2. Save the **bot token** it gives you
3. Send your new bot any message to start the chat
4. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` → find `"chat": {"id": ...}` — that's your chat ID

### 2. Notion integration

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations) → **New integration**
2. Copy the **integration token** (starts with `ntn_`)
3. Open your to-do page in Notion → `...` menu → **Connections** → add your integration
4. Copy the **page ID** from the URL — it's the hex string at the end, e.g. `3170987e29b580bc83c8c7ee98c07ee9`

### 3. GitHub secrets

In your repo go to **Settings → Secrets and variables → Actions** and add:

| Secret | Value |
|--------|-------|
| `NOTION_TOKEN` | Your `ntn_...` integration token |
| `NOTION_DATABASE_ID` | Your Notion page ID |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |

## Running locally

```bash
cp .env.example .env
# Fill in your credentials in .env
pip install -r requirements.txt
python main.py
```

## Schedule

The brief runs daily at **7am UTC** (7am GMT / 8am BST).

To change the time, edit the cron expression in [.github/workflows/daily_brief.yml](.github/workflows/daily_brief.yml):

```yaml
- cron: '0 7 * * *'  # minute hour * * *
```

UK timezone reference:
- Winter (GMT): `0 7 * * *`
- Summer (BST): `0 6 * * *`

## Triggering manually

Go to the **Actions** tab in your GitHub repo → **Daily Brief** → **Run workflow**.

## Project structure

```
├── main.py                          # Entry point
├── notion_fetcher.py                # Reads to-dos from Notion
├── telegram_sender.py               # Sends the Telegram message
├── .github/workflows/daily_brief.yml  # GitHub Actions cron job
├── requirements.txt
└── .env.example                     # Template for local credentials
```

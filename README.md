# Daily Brief

A Python script that sends a daily morning Telegram message with an AI-generated focus recommendation, Google Calendar events, smart task management, important emails filtered by AI, a markets brief, and a personal portfolio snapshot. Runs automatically via GitHub Actions — no server required.

## What it sends

- **Focus for Today** — a one-sentence AI recommendation of the single most important thing to work on, prioritising deadlines and business tasks
- **Today's calendar** — events from Google Calendar with start and end times
- **Today's tasks** — tasks carried over from yesterday plus anything moved from Tomorrow
- **Recurring habits** — daily habits that auto-reset to unchecked every morning
- **Emails** — unread emails from your Primary inbox, filtered by Claude AI to surface only the ones that need your attention
- **Markets** — a structured snapshot (S&P 500, FTSE 100, Mag 7 aggregate, Bitcoin) plus a 7–8 sentence AI-generated summary of what drove the moves, sourced from top-tier financial outlets
- **Portfolio** — high-level summary of each Trading 212 account (total value, daily %, unrealised P&L, cash)
- *LinkedIn integration coming soon*

## Daily task reset (runs at 6am UTC)

Each morning the workflow automatically:
1. **Resets** all Recurring Tasks to unchecked
2. **Carries over** any uncompleted Today tasks (completed ones are deleted)
3. **Moves** everything from Tomorrow into Today, then clears Tomorrow
4. Sends the brief with the updated task list

## Setup

### 1. Telegram bot

1. Message `@BotFather` on Telegram → `/newbot` → follow the prompts
2. Save the **bot token** it gives you
3. Send your new bot any message to start the chat
4. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` → find `"chat": {"id": ...}` — that's your chat ID

### 2. Notion integration

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations) → **New integration**
2. Copy the **integration token** (starts with `ntn_`)
3. Open your Notion page → `...` menu → **Connections** → add your integration
4. Copy the **page ID** from the URL — it's the hex string at the end, e.g. `3170987e29b580bc83c8c7ee98c07ee9`

**Page structure required:** The Notion page must have three **toggle headings** (use `/toggle heading 1` in Notion) with these exact names:

```
▶ Recurring Tasks
   ☐ Send 15 connection requests
▶ Today
   ☐ Call the client
▶ Tomorrow
   ☐ Write blog post
```

> The headings must be **toggle headings** (not regular headings) so tasks can be nested inside them as children. Add tasks by pressing Enter inside the toggle.

### 3. Google Calendar

1. Go to [console.cloud.google.com](https://console.cloud.google.com) → create a new project (e.g. "Daily Brief")
2. Search for **Google Calendar API** → enable it
3. Go to **IAM & Admin → Service Accounts → Create service account**
4. Give it a name (e.g. "daily-brief") → click through without assigning a role → done
5. Click the service account → **Keys** tab → **Add Key → Create new key → JSON** → download the file
6. Open [Google Calendar](https://calendar.google.com) → **Settings** (gear) → find your calendar under **Settings for my calendars**
7. **Share with specific people** → add the `client_email` from the JSON file → **See all event details**
8. Copy your **Calendar ID** from the same settings page (usually your Gmail address)

### 4. Gmail

1. In the same Google Cloud project, enable the **Gmail API** (APIs & Services → Library → search "Gmail API")
2. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
3. Application type: **Desktop app** → name it anything → Create
4. Copy the **Client ID** and **Client Secret** into your `.env` file
5. Go to **OAuth consent screen → Test users** → add your Gmail address
6. Run the one-time auth script to get your refresh token:
   ```bash
   python gmail_auth.py
   ```
   Your browser opens — log in and grant access. Copy the printed `GMAIL_REFRESH_TOKEN` into your `.env`.

> **Note:** To prevent the refresh token expiring after 7 days, go to the OAuth consent screen and change Publishing status from **Testing → In production**. No Google review is needed for a personal app.

### 5. Anthropic API key

1. Go to [console.anthropic.com](https://console.anthropic.com) → **API Keys → Create key**
2. Copy it into your `.env` as `ANTHROPIC_API_KEY`

### 6. Trading 212 (read-only)

The brief pulls a high-level summary for each account. You need a separate API key per account.

1. Open the Trading 212 app → **Settings → API (Beta)**
2. Create a key for your **Stocks & Shares ISA** — copy the key and secret immediately (secret shown once)
3. Create a second key for your **Invest** account — copy both values
4. Add all four values to your `.env` and GitHub secrets

> Only read permissions are used. No order placement or trading functionality is implemented.

### 7. GitHub secrets

In your repo go to **Settings → Secrets and variables → Actions** and add:

| Secret | Value |
|--------|-------|
| `NOTION_TOKEN` | Your `ntn_...` integration token |
| `NOTION_DATABASE_ID` | Your Notion page ID |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |
| `GOOGLE_CALENDAR_ID` | Your calendar ID (usually your Gmail address) |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | The full contents of the downloaded JSON key file |
| `GMAIL_CLIENT_ID` | From Google Cloud OAuth credentials |
| `GMAIL_CLIENT_SECRET` | From Google Cloud OAuth credentials |
| `GMAIL_REFRESH_TOKEN` | Printed by `gmail_auth.py` |
| `ANTHROPIC_API_KEY` | From console.anthropic.com |
| `TRADING212_ISA_KEY` | Trading 212 ISA API key |
| `TRADING212_ISA_SECRET` | Trading 212 ISA API secret |
| `TRADING212_INVEST_KEY` | Trading 212 Invest API key |
| `TRADING212_INVEST_SECRET` | Trading 212 Invest API secret |

## Running locally

```bash
cp .env.example .env
# Fill in your credentials in .env
pip install -r requirements.txt
python main.py
```

## Schedule

The brief runs daily at **6am UTC** (6am GMT / 7am BST).

To change the time, edit the cron expression in [.github/workflows/daily_brief.yml](.github/workflows/daily_brief.yml):

```yaml
- cron: '0 6 * * *'  # minute hour * * *
```

UK timezone reference:
- Winter (GMT): `0 6 * * *`
- Summer (BST): `0 5 * * *`

## Triggering manually

Go to the **Actions** tab in your GitHub repo → **Daily Brief** → **Run workflow**.

## Project structure

```
├── main.py                            # Entry point
├── notion_manager.py                  # Reads and resets the three-section Notion task page
├── calendar_fetcher.py                # Reads today's events from Google Calendar
├── email_fetcher.py                   # Fetches Gmail and filters with Claude AI
├── focus_generator.py                 # Generates AI focus recommendation with Claude
├── market_fetcher.py                  # Fetches market data (yfinance) + AI market brief
├── portfolio_fetcher.py               # Reads Trading 212 account summaries (read-only)
├── gmail_auth.py                      # One-time script to get Gmail refresh token
├── telegram_sender.py                 # Sends the Telegram message
├── .github/workflows/daily_brief.yml  # GitHub Actions cron job
├── requirements.txt
└── .env.example                       # Template for local credentials
```

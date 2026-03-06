import os
import requests
from datetime import date, timedelta

import anthropic
import yfinance as yf

INDICES = {
    "^GSPC": "S&P 500",
    "^FTSE": "FTSE 100",
}

MAG7 = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Google",
    "AMZN": "Amazon",
    "META": "Meta",
    "NVDA": "Nvidia",
    "TSLA": "Tesla",
}


def get_market_brief() -> str:
    """
    Fetch yesterday's market data, then use Claude with web search to generate
    a structured summary of what drove the moves.

    Returns a formatted string including the data snapshot and AI summary,
    or "" on any failure so the rest of the brief still sends.
    """
    try:
        return _fetch_and_generate()
    except Exception as e:
        print(f"[market_fetcher] Error: {e}")
        return ""


def _fetch_and_generate() -> str:
    market_data = _fetch_market_data()

    if not market_data:
        return ""

    snapshot = _build_snapshot(market_data)
    summary = _generate_summary(market_data)

    lines = ["📈 *MARKETS*", "", snapshot]
    if summary:
        lines += ["", summary]

    return "\n".join(lines)


def _fetch_market_data() -> dict:
    """Fetch daily % change and closing price for all tickers."""
    results = {}

    # Fetch up to but not including today — guarantees iloc[-1] is last completed session
    end = date.today()
    start = end - timedelta(days=10)

    # Indices and Mag 7 via yfinance
    for symbol, name in {**INDICES, **MAG7}.items():
        try:
            hist = yf.Ticker(symbol).history(start=str(start), end=str(end))
            if len(hist) >= 2:
                last = hist["Close"].iloc[-1]
                prev = hist["Close"].iloc[-2]
                pct = (last - prev) / prev * 100
                results[name] = {"price": last, "pct": pct}
        except Exception:
            pass  # skip this ticker silently

    # Bitcoin via CoinGecko (more accurate daily closes than yfinance for crypto)
    btc = _fetch_bitcoin_coingecko()
    if btc:
        results["Bitcoin"] = btc

    return results


def _fetch_bitcoin_coingecko() -> dict | None:
    """
    Fetch yesterday's Bitcoin close and daily % change from CoinGecko's free API.
    Uses the /market_chart endpoint which returns daily OHLC data in UTC.
    """
    try:
        resp = requests.get(
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
            params={"vs_currency": "usd", "days": "3", "interval": "daily"},
            timeout=10,
        )
        resp.raise_for_status()
        prices = resp.json().get("prices", [])  # [[timestamp_ms, price], ...]

        # prices[-1] is today (partial), prices[-2] is yesterday's close, prices[-3] is day before
        if len(prices) >= 3:
            yesterday_price = prices[-2][1]
            prev_price = prices[-3][1]
            pct = (yesterday_price - prev_price) / prev_price * 100
            return {"price": yesterday_price, "pct": pct}
    except Exception:
        pass
    return None


def _arrow(pct: float) -> str:
    return "↑" if pct >= 0 else "↓"


def _fmt_pct(pct: float) -> str:
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def _build_snapshot(data: dict) -> str:
    lines = []

    # Indices
    for name in ("S&P 500", "FTSE 100"):
        if name in data:
            d = data[name]
            lines.append(f"{name} — {d['price']:,.0f} pts  {_arrow(d['pct'])} {_fmt_pct(d['pct'])}")

    # Mag 7 aggregate
    mag7_pcts = [data[n]["pct"] for n in MAG7.values() if n in data]
    if mag7_pcts:
        avg = sum(mag7_pcts) / len(mag7_pcts)
        lines.append(f"Mag 7 — avg  {_arrow(avg)} {_fmt_pct(avg)}")

    # Bitcoin
    if "Bitcoin" in data:
        d = data["Bitcoin"]
        lines.append(f"Bitcoin — ${d['price']:,.0f}  {_arrow(d['pct'])} {_fmt_pct(d['pct'])}")

    return "\n".join(lines)


def _generate_summary(data: dict) -> str:
    """Call Claude with web search to write the market summary."""
    # Format individual Mag 7 data for the prompt (context only, not displayed)
    mag7_lines = "\n".join(
        f"- {name}: {_fmt_pct(data[name]['pct'])}"
        for name in MAG7.values()
        if name in data
    )

    index_lines = "\n".join(
        f"- {name}: {data[name]['price']:,.0f} pts ({_fmt_pct(data[name]['pct'])})"
        for name in ("S&P 500", "FTSE 100")
        if name in data
    )

    btc_line = ""
    if "Bitcoin" in data:
        d = data["Bitcoin"]
        btc_line = f"- Bitcoin: ${d['price']:,.0f} ({_fmt_pct(d['pct'])})"

    prompt = f"""You are writing the markets section of a daily brief for a business founder.

Yesterday's closing data:

Indices:
{index_lines or "No data"}

Mag 7 tech stocks (individual data for context):
{mag7_lines or "No data"}

Crypto:
{btc_line or "No data"}

Using web search, find out what drove these market moves yesterday. Write a structured summary using exactly these four bold headers, each followed by 1–3 sentences:

*US:* [What drove S&P 500 performance — key macro events, sectors, or stocks]
*UK:* [What drove FTSE 100 performance — key macro events, sectors, or stocks]
*Tech:* [The most notable 1–2 Mag 7 movers and why]
*Bitcoin:* [One sentence on Bitcoin]

Rules:
- Only include claims you can verify from at least one reputable financial source (Reuters, Bloomberg, CNBC, Financial Times, BBC Business, Wall Street Journal, MarketWatch)
- Ignore blogs, forums, social media, and opinion pieces
- Assume the reader understands markets — no jargon explanations needed
- Use the exact header format shown (*US:*, *UK:*, *Tech:*, *Bitcoin:*) — these render as bold in Telegram
- Start your response immediately with *US:* — no preamble, no intro sentence, no date line, no separators"""

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 5,
        }],
        messages=[{"role": "user", "content": prompt}],
    )

    # Concatenate all text blocks (web_search_tool_result blocks are non-text)
    full_text = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()

    # Strip any preamble before the first section header
    marker = "*US:"
    idx = full_text.find(marker)
    return full_text[idx:] if idx != -1 else full_text

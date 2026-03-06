import base64
import os
from datetime import date, timedelta

import requests
import yfinance as yf

BASE_URL = "https://live.trading212.com/api/v0"

CURRENCY_SYMBOLS = {"GBP": "£", "EUR": "€", "USD": "$"}

ACCOUNTS = [
    ("TRADING212_ISA_KEY", "TRADING212_ISA_SECRET", "Stocks & Shares ISA"),
    ("TRADING212_INVEST_KEY", "TRADING212_INVEST_SECRET", "Invest"),
]


def get_portfolio_summary() -> str:
    """
    Fetch high-level account summaries from Trading 212 (read-only).
    Returns a formatted string with a section per account, or "" if both fail.
    """
    sections = []

    for key_var, secret_var, label in ACCOUNTS:
        api_key = os.environ.get(key_var, "")
        api_secret = os.environ.get(secret_var, "")

        if not api_key or not api_secret:
            continue  # account not configured — skip silently

        try:
            section = _fetch_account(api_key, api_secret, label)
            if section:
                sections.append(section)
        except Exception as e:
            print(f"[portfolio_fetcher] {label} error: {e}")

    if not sections:
        return ""

    return "💰 *PORTFOLIO*\n\n" + "\n\n".join(sections)


def _fetch_account(api_key: str, api_secret: str, label: str) -> str:
    headers = {
        "Authorization": "Basic " + base64.b64encode(
            f"{api_key}:{api_secret}".encode()
        ).decode()
    }

    # Account summary
    summary_resp = requests.get(
        f"{BASE_URL}/equity/account/summary", headers=headers, timeout=10
    )
    summary_resp.raise_for_status()
    summary = summary_resp.json()

    total_value = summary.get("totalValue", 0)
    cash = summary.get("cash", {}).get("availableToTrade", 0)
    unrealised_pnl = summary.get("investments", {}).get("unrealizedProfitLoss", 0)
    total_cost = summary.get("investments", {}).get("totalCost", 0)
    currency = summary.get("currency", "GBP")
    sym = CURRENCY_SYMBOLS.get(currency, "£")

    # All-time P&L %
    alltime_pct = (unrealised_pnl / total_cost * 100) if total_cost else None

    # Daily % — weighted average via yfinance
    daily_pct = _calc_daily_pct(headers, summary)

    # Build output lines
    lines = [f"*{label}*"]

    total_str = f"{sym}{total_value:,.2f}"
    if daily_pct is not None:
        sign = "+" if daily_pct >= 0 else ""
        total_str += f" ({sign}{daily_pct:.1f}% today)"
    lines.append(f"Total value: {total_str}")

    pnl_sign = "+" if unrealised_pnl >= 0 else ""
    alltime_str = f"{pnl_sign}{sym}{abs(unrealised_pnl):,.2f}"
    if alltime_pct is not None:
        pnl_sign2 = "+" if alltime_pct >= 0 else ""
        alltime_str += f" ({pnl_sign2}{alltime_pct:.1f}% all-time)"
    lines.append(f"Unrealised P&L: {alltime_str}")

    lines.append(f"Cash: {sym}{cash:,.2f}")

    return "\n".join(lines)


def _calc_daily_pct(headers: dict, summary: dict) -> float | None:
    """
    Calculate today's portfolio daily % change by weighting each position's
    yfinance daily % change by its current value. Returns None if unavailable.
    """
    try:
        positions_resp = requests.get(
            f"{BASE_URL}/equity/positions", headers=headers, timeout=15
        )
        positions_resp.raise_for_status()
        positions = positions_resp.json()

        if not positions:
            return None

        total_invested = summary.get("investments", {}).get("currentValue", 0)
        if not total_invested:
            return None

        weighted_sum = 0.0
        covered_value = 0.0

        for pos in positions:
            t212_ticker = pos.get("ticker", "")
            quantity = pos.get("quantity", 0)
            current_price = pos.get("currentPrice", 0)
            pos_value = quantity * current_price

            yf_ticker = _to_yf_ticker(t212_ticker)
            daily_pct = _yf_daily_pct(yf_ticker)

            if daily_pct is not None and pos_value > 0:
                weighted_sum += daily_pct * pos_value
                covered_value += pos_value

        if covered_value == 0:
            return None

        return weighted_sum / covered_value

    except Exception:
        return None


def _to_yf_ticker(t212_ticker: str) -> str:
    """
    Convert Trading 212 ticker format to yfinance format.
    AAPL_US_EQ  → AAPL
    LLOY_LON_EQ → LLOY.L
    """
    parts = t212_ticker.split("_")
    if len(parts) >= 2:
        base, exchange = parts[0], parts[1]
        if exchange == "LON":
            return f"{base}.L"
        return base
    return t212_ticker


def _yf_daily_pct(ticker: str) -> float | None:
    try:
        end = date.today()
        start = end - timedelta(days=10)
        hist = yf.Ticker(ticker).history(start=str(start), end=str(end))
        if len(hist) >= 2:
            last = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[-2]
            return (last - prev) / prev * 100
    except Exception:
        pass
    return None

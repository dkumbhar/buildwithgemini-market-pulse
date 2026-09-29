# Copyright 2026 Google LLC
# Firestore portfolio tools & market analytics for MarketPulse agent

import json
import os
import urllib.request
from typing import Any
from google.cloud import firestore

FIRESTORE_PROJECT_ID = "qwiklabs-gcp-01-f582106045c5"


def _get_db():
    return firestore.Client(project=FIRESTORE_PROJECT_ID)


def get_portfolio() -> list[dict[str, Any]]:
    """Retrieves all assets/holdings in the user's investment portfolio from Firestore.

    Returns:
        A list of dictionaries representing portfolio holdings with fields like ticker,
        name, asset_type, shares, avg_buy_price, current_price, and category.
    """
    db = _get_db()
    docs = db.collection("portfolio").stream()
    portfolio = [doc.to_dict() for doc in docs]
    return portfolio


def get_asset_details(ticker: str) -> dict[str, Any] | str:
    """Retrieves details for a specific stock/crypto ticker from the portfolio in Firestore.

    Args:
        ticker: The ticker symbol (e.g., 'AAPL', 'GOOGL', 'BTC', 'ETH').

    Returns:
        A dictionary containing the asset details if found, or an error message if not found.
    """
    db = _get_db()
    doc_ref = db.collection("portfolio").document(ticker.upper())
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    return f"Asset '{ticker.upper()}' not found in your portfolio."


def add_or_update_portfolio_item(
    ticker: str,
    name: str,
    asset_type: str,
    shares: float,
    avg_buy_price: float,
    current_price: float,
    category: str = "General",
) -> str:
    """Adds a new stock/crypto asset or updates an existing holding in the Firestore portfolio.

    Args:
        ticker: Ticker symbol (e.g., 'AAPL', 'NVDA', 'BTC').
        name: Full company or asset name (e.g., 'Apple Inc.', 'Bitcoin').
        asset_type: Type of asset ('Stock', 'Crypto', 'ETF', 'Bond').
        shares: Number of shares or units held.
        avg_buy_price: Average buy price per share/unit.
        current_price: Current market price per share/unit.
        category: Category or sector (e.g., 'Technology', 'Crypto', 'Index ETF').

    Returns:
        Confirmation message indicating success.
    """
    db = _get_db()
    item_data = {
        "ticker": ticker.upper(),
        "name": name,
        "asset_type": asset_type,
        "shares": float(shares),
        "avg_buy_price": float(avg_buy_price),
        "current_price": float(current_price),
        "category": category,
    }
    db.collection("portfolio").document(ticker.upper()).set(item_data)
    return f"Successfully added/updated {ticker.upper()} ({name}) in portfolio."


def calculate_portfolio_performance() -> dict[str, Any]:
    """Calculates comprehensive performance metrics for the user's portfolio holdings.

    Computes total portfolio market value, total cost basis, total unrealized profit/loss,
    percentage ROI, asset class distribution, and top/worst performing assets.

    Returns:
        A dictionary containing calculated portfolio performance metrics.
    """
    portfolio = get_portfolio()
    if not portfolio:
        return {"error": "Portfolio is empty."}

    total_value = 0.0
    total_cost = 0.0
    asset_type_values: dict[str, float] = {}
    performers = []

    for item in portfolio:
        shares = item.get("shares", 0.0)
        buy_price = item.get("avg_buy_price", 0.0)
        current_price = item.get("current_price", 0.0)
        asset_type = item.get("asset_type", "Other")
        ticker = item.get("ticker", "UNKNOWN")

        item_value = shares * current_price
        item_cost = shares * buy_price
        gain_loss = item_value - item_cost
        gain_loss_pct = (gain_loss / item_cost * 100) if item_cost > 0 else 0.0

        total_value += item_value
        total_cost += item_cost
        asset_type_values[asset_type] = asset_type_values.get(asset_type, 0.0) + item_value

        performers.append({
            "ticker": ticker,
            "name": item.get("name", ticker),
            "value": round(item_value, 2),
            "gain_loss": round(gain_loss, 2),
            "gain_loss_pct": round(gain_loss_pct, 2),
        })

    performers.sort(key=lambda x: x["gain_loss_pct"], reverse=True)
    total_gain_loss = total_value - total_cost
    total_gain_loss_pct = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0.0

    allocation_pct = {
        asset_type: round((val / total_value * 100), 2)
        for asset_type, val in asset_type_values.items()
    }

    return {
        "total_portfolio_value": round(total_value, 2),
        "total_cost_basis": round(total_cost, 2),
        "total_unrealized_profit_loss": round(total_gain_loss, 2),
        "overall_roi_percentage": round(total_gain_loss_pct, 2),
        "asset_allocation": allocation_pct,
        "best_performer": performers[0] if performers else None,
        "worst_performer": performers[-1] if performers else None,
        "holdings_count": len(portfolio),
    }


def fetch_market_quote(ticker: str) -> dict[str, Any]:
    """Fetches real-time or current market price quote, day change, and volume for a ticker.

    Args:
        ticker: The stock or crypto ticker symbol (e.g., 'AAPL', 'GOOGL', 'BTC', 'ETH', 'NVDA').

    Returns:
        A dictionary with live market quote data including symbol, price, day change, and high/low.
    """
    clean_ticker = ticker.upper().strip()
    existing_asset = get_asset_details(clean_ticker)

    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{clean_ticker}?interval=1d&range=1d"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            result = data["chart"]["result"][0]
            meta = result["meta"]
            current_price = meta.get("regularMarketPrice")
            prev_close = meta.get("previousClose") or meta.get("chartPreviousClose")

            day_change = (current_price - prev_close) if (current_price and prev_close) else 0.0
            day_change_pct = (day_change / prev_close * 100) if prev_close else 0.0

            return {
                "symbol": clean_ticker,
                "name": meta.get("shortName") or meta.get("symbol", clean_ticker),
                "current_price": round(current_price, 2),
                "previous_close": round(prev_close, 2) if prev_close else None,
                "day_change": round(day_change, 2),
                "day_change_pct": round(day_change_pct, 2),
                "currency": meta.get("currency", "USD"),
                "high": round(meta.get("regularMarketDayHigh", current_price), 2) if current_price else None,
                "low": round(meta.get("regularMarketDayLow", current_price), 2) if current_price else None,
                "source": "Yahoo Finance (Live API)",
            }
    except Exception:
        if isinstance(existing_asset, dict):
            price = existing_asset.get("current_price", 0.0)
            return {
                "symbol": clean_ticker,
                "name": existing_asset.get("name", clean_ticker),
                "current_price": price,
                "previous_close": existing_asset.get("avg_buy_price", price),
                "day_change": round(price - existing_asset.get("avg_buy_price", price), 2),
                "day_change_pct": round(
                    ((price - existing_asset.get("avg_buy_price", price)) / existing_asset.get("avg_buy_price", price) * 100), 2
                ) if existing_asset.get("avg_buy_price", 0) > 0 else 0.0,
                "currency": "USD",
                "source": "MarketPulse Database (Fallback)",
            }
        return {
            "symbol": clean_ticker,
            "name": clean_ticker,
            "current_price": 150.00,
            "day_change": 2.50,
            "day_change_pct": 1.69,
            "currency": "USD",
            "source": "MarketPulse Simulated Quote",
        }


def simulate_investment_growth(
    initial_amount: float,
    monthly_deposit: float,
    annual_return_pct: float,
    years: int,
) -> dict[str, Any]:
    """Simulates compound growth for an investment portfolio over a specified time horizon.

    Calculates projected future balance, total contributions, total interest/gains earned,
    and year-by-year milestone balances.

    Args:
        initial_amount: Starting capital amount in USD (e.g., 10000.0).
        monthly_deposit: Recurring monthly contribution in USD (e.g., 500.0).
        annual_return_pct: Expected annual return rate percentage (e.g., 7.5 for 7.5%).
        years: Investment duration in years (e.g., 10).

    Returns:
        A dictionary containing projected total balance, interest earned, and annual breakdown.
    """
    r = (annual_return_pct / 100.0) / 12.0
    current_balance = float(initial_amount)
    total_contributions = float(initial_amount)
    annual_milestones = []

    for month in range(1, (years * 12) + 1):
        interest_this_month = current_balance * r
        current_balance += interest_this_month + monthly_deposit
        total_contributions += monthly_deposit

        if month % 12 == 0:
            year_num = month // 12
            annual_milestones.append({
                "year": year_num,
                "balance": round(current_balance, 2),
                "contributions": round(total_contributions, 2),
                "interest_earned": round(current_balance - total_contributions, 2),
            })

    total_interest = current_balance - total_contributions

    return {
        "initial_amount": round(initial_amount, 2),
        "monthly_deposit": round(monthly_deposit, 2),
        "annual_return_pct": annual_return_pct,
        "duration_years": years,
        "final_projected_balance": round(current_balance, 2),
        "total_contributions": round(total_contributions, 2),
        "total_interest_earned": round(total_interest, 2),
        "annual_milestones": annual_milestones,
    }


def fetch_exchange_rates(
    base_currency: str = "USD",
    target_currencies: str = "EUR,GBP,JPY,CAD,AUD,BTC",
) -> dict[str, Any]:
    """Fetches real-time foreign exchange and cryptocurrency rates for a base currency.

    Uses public market exchange endpoints. Reads optional API key from
    EXCHANGE_RATE_API_KEY environment variable if present.

    Args:
        base_currency: Base currency code (e.g. 'USD', 'EUR', 'GBP').
        target_currencies: Comma-separated list of target currency/crypto symbols (e.g. 'EUR,GBP,JPY,BTC').

    Returns:
        A dictionary containing the base currency, exchange rates, and source metadata.
    """
    api_key = os.environ.get("EXCHANGE_RATE_API_KEY") or os.environ.get("FINANCE_API_KEY")
    base = base_currency.upper().strip()
    targets = [t.strip().upper() for t in target_currencies.split(",") if t.strip()]

    url = f"https://api.coinbase.com/v2/exchange-rates?currency={base}"
    headers = {"User-Agent": "MarketPulse/1.0"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())["data"]
            all_rates = data.get("rates", {})
            rates = {t: float(all_rates[t]) for t in targets if t in all_rates}

            return {
                "base_currency": base,
                "rates": rates,
                "api_key_provided": bool(api_key),
                "source": "Coinbase Exchange Rates API",
            }
    except Exception as e:
        return {
            "error": f"Failed to fetch exchange rates: {str(e)}",
            "base_currency": base,
        }

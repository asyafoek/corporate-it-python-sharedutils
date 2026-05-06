"""
massive_utils.py
Unified utilities for market data (stocks, ETFs, crypto).
Supports Polygon-style APIs + basic normalization + helpers.
"""

import os
import requests
from typing import List, Dict, Any, Optional
from format_utils import pretty_print


# -----------------------------
# Config
# -----------------------------

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

POLYGON_BASE = "https://api.polygon.io"

HEADERS = {
    "Authorization": f"Bearer {POLYGON_API_KEY}" if POLYGON_API_KEY else ""
}


def get_market_tickers(market):
    # https://api.massive.com/v3/reference/tickers?market=stocks&active=true&order=asc&limit=100&sort=ticker&apiKey=yIiDcOmJ5j5Ug0dJfjkKiOLJR7kwOVwJ"
    url = f"https://api.massive.com/v3/reference/tickers"
    results = []

    params = {
            "market": market, 
            "order": "asc",
            "limit": "1000",
            "active": "true"
        }

    while True:
        resp = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        data = resp.json()

        results.extend(data.get("results", []))

        next_url = data.get("next_url")
        if not next_url:
            break

        url = next_url
        params = None

    return results


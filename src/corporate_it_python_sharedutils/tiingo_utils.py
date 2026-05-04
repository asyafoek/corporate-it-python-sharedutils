import os
import requests
import json
from datetime import datetime, timezone, timedelta
from common.format_utils import pretty_print

API_KEY = os.getenv("TIINGO_API_KEY")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Token {API_KEY}"
}


def get_news(ticker):

    # today's date (UTC)
    # today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=1)

    url = "https://api.tiingo.com/tiingo/news"

    params = {
        "tickers": ticker,
        "startDate": start.strftime("%Y-%m-%d"),
        "endDate": end.strftime("%Y-%m-%d"),
    }
    # print(params)

    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()
    return pretty_print(data)




SIGNAL_COLUMNS = [
    "signal_id",
    "run_id",

    "signal",
    "side",

    "rule_name",

    "reward_risk_ratio",

    "confidence",

    "market_timestamp",
    "signal_generated_at",
    "timestamp_precision",

    "market_snapshot",

    "profile_snapshot",

    "watchlist_entry_snapshot",

    "open_orders_snapshot",

    "evaluation"
]

SIGNAL_BUY = "Buy"
SIGNAL_SELL = "Sell"
SIGNAL_HOLD = "Hold"
SIGNAL_WAIT = "Wait"

SIDE_LONG = "Long"
SIDE_SHORT = "Short"

TRADING_STATE_ACTIVE = "Active"
TRADING_STATE_CLOSE_ONLY = "CloseOnly"
TRADING_STATE_DISABLED = "Disabled"
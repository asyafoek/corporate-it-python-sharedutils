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

SIGNAL_BUY = "buy"
SIGNAL_SELL = "sell"
SIGNAL_HOLD = "hold"
SIGNAL_WAIT = "wait"

SIDE_LONG = "long"
SIDE_SHORT = "short"

TRADING_STATE_ACTIVE = "active"
TRADING_STATE_CLOSE_ONLY = "close_only"
TRADING_STATE_DISABLED = "disabled"
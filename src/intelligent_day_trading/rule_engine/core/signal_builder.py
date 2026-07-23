import uuid

import pandas as pd

from .timestamp_helper import (
    TimestampHelper
)


def build_signal(
    *,
    profile: dict,
    watchlist_entry: dict,
    market_data,
    open_orders,
    signal: str,
    side: str,
    rule_name: str,
    reward_risk_ratio: float,
    confidence: float,
    evaluation: dict
) -> dict:

    row = market_data.iloc[-1]

    timestamp = pd.Timestamp(
        row.name
    )

    precision = (
        TimestampHelper.detect_precision(
            timestamp
        )
    )

    return {

        "signal_id":
            str(uuid.uuid4()),

        "run_id":
            watchlist_entry["run_id"],

        "signal":
            signal,

        "side":
            side,

        "rule_name":
            rule_name,

        "reward_risk_ratio":
            reward_risk_ratio,

        "confidence":
            confidence,

        "market_timestamp":
            TimestampHelper.market_timestamp(
                timestamp,
                precision
            ),

        "signal_generated_at":
            TimestampHelper.signal_timestamp(
                precision
            ),

        "timestamp_precision":
            precision,

        "market_snapshot":
            row.to_dict(),

        "profile_snapshot":
            profile,

        "watchlist_entry_snapshot":
            watchlist_entry,

        "open_orders_snapshot":
            (
                open_orders.to_dict(
                    orient="records"
                )
                if open_orders is not None
                else []
            ),

        "evaluation":
            evaluation
    }
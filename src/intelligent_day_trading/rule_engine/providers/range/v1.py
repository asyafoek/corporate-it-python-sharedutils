from intelligent_day_trading.rule_engine.core.confidence import (
    ConfidenceCalculator
)
from intelligent_day_trading.rule_engine.core.constants import (
    SIGNAL_BUY,
    SIGNAL_SELL,
    SIGNAL_WAIT,
    SIDE_LONG,
    SIDE_SHORT
)
from intelligent_day_trading.rule_engine.core.signal_provider import (
    SignalProvider
)


class RangeProvider(
    SignalProvider
):

    LONG_WEIGHTS = {
        "close_near_low_20": 0.40,
        "rsi_lt_40": 0.30,
        "volume_ratio_gt_1": 0.30
    }

    SHORT_WEIGHTS = {
        "close_near_high_20": 0.40,
        "rsi_gt_60": 0.30,
        "volume_ratio_gt_1": 0.30
    }

    def evaluate(
        self,
        profile,
        watchlist_entry,
        market_data,
        open_orders
    ):

        row = market_data.iloc[-1]

        close = float(
            row["c"]
        )

        low_20 = float(
            row["low_20"]
        )

        high_20 = float(
            row["high_20"]
        )

        distance_from_low = (
            abs(close - low_20)
            / low_20
        )

        distance_from_high = (
            abs(close - high_20)
            / high_20
        )

        long_conditions = {

            "close_near_low_20":
                distance_from_low <= 0.01,

            "rsi_lt_40":
                float(
                    row["rsi14"]
                ) < 40.0,

            "volume_ratio_gt_1":
                float(
                    row["volume_ratio"]
                ) > 1.0
        }

        short_conditions = {

            "close_near_high_20":
                distance_from_high <= 0.01,

            "rsi_gt_60":
                float(
                    row["rsi14"]
                ) > 60.0,

            "volume_ratio_gt_1":
                float(
                    row["volume_ratio"]
                ) > 1.0
        }

        long_confidence = (
            ConfidenceCalculator.calculate(
                long_conditions,
                self.LONG_WEIGHTS
            )
        )

        short_confidence = (
            ConfidenceCalculator.calculate(
                short_conditions,
                self.SHORT_WEIGHTS
            )
        )

        results = []

        if any(
            long_conditions.values()
        ):

            results.append({

                "provider":
                    "range",

                "side":
                    SIDE_LONG,

                "signal":
                    SIGNAL_BUY
                    if all(
                        long_conditions.values()
                    )
                    else SIGNAL_WAIT,

                "validations":
                    long_confidence.validations
            })

        if any(
            short_conditions.values()
        ):

            results.append({

                "provider":
                    "range",

                "side":
                    SIDE_SHORT,

                "signal":
                    SIGNAL_SELL
                    if all(
                        short_conditions.values()
                    )
                    else SIGNAL_WAIT,

                "validations":
                    short_confidence.validations
            })

        return results
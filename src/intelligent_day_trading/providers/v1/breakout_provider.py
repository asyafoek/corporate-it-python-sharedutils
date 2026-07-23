from intelligent_day_trading.core.confidence import (
    ConfidenceCalculator
)
from intelligent_day_trading.core.constants import (
    SIGNAL_BUY,
    SIGNAL_SELL,
    SIGNAL_WAIT,
    SIDE_LONG,
    SIDE_SHORT
)
from intelligent_day_trading.core.signal_provider import (
    SignalProvider
)


class BreakoutProvider(
    SignalProvider
):

    LONG_WEIGHTS = {
        "close_gt_high_20": 0.50,
        "volume_ratio_gt_2": 0.30,
        "rsi_gt_60": 0.20
    }

    SHORT_WEIGHTS = {
        "close_lt_low_20": 0.50,
        "volume_ratio_gt_2": 0.30,
        "rsi_lt_40": 0.20
    }

    def evaluate(
        self,
        profile,
        watchlist_entry,
        market_data,
        open_orders
    ):

        row = market_data.iloc[-1]

        long_conditions = {

            "close_gt_high_20":
                float(
                    row["c"]
                ) > float(
                    row["high_20"]
                ),

            "volume_ratio_gt_2":
                float(
                    row["volume_ratio"]
                ) > 2.0,

            "rsi_gt_60":
                float(
                    row["rsi14"]
                ) > 60.0
        }

        short_conditions = {

            "close_lt_low_20":
                float(
                    row["c"]
                ) < float(
                    row["low_20"]
                ),

            "volume_ratio_gt_2":
                float(
                    row["volume_ratio"]
                ) > 2.0,

            "rsi_lt_40":
                float(
                    row["rsi14"]
                ) < 40.0
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
                    "breakout",

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
                    "breakout",

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
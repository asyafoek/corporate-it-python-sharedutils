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


class ReversalProvider(
    SignalProvider
):

    LONG_WEIGHTS = {
        "rsi_lt_25": 0.40,
        "close_gt_ema8": 0.30,
        "volume_ratio_gt_1_5": 0.30
    }

    SHORT_WEIGHTS = {
        "rsi_gt_75": 0.40,
        "close_lt_ema8": 0.30,
        "volume_ratio_gt_1_5": 0.30
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

            "rsi_lt_25":
                float(
                    row["rsi14"]
                ) < 25.0,

            "close_gt_ema8":
                float(
                    row["c"]
                ) > float(
                    row["ema8"]
                ),

            "volume_ratio_gt_1_5":
                float(
                    row["volume_ratio"]
                ) > 1.5
        }

        short_conditions = {

            "rsi_gt_75":
                float(
                    row["rsi14"]
                ) > 75.0,

            "close_lt_ema8":
                float(
                    row["c"]
                ) < float(
                    row["ema8"]
                ),

            "volume_ratio_gt_1_5":
                float(
                    row["volume_ratio"]
                ) > 1.5
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
                    "reversal",

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
                    "reversal",

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
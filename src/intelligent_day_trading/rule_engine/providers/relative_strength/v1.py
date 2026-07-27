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


class RelativeStrengthProvider(
    SignalProvider
):

    LONG_WEIGHTS = {
        "relative_strength_gt_1": 0.50,
        "close_gt_ema20": 0.30,
        "volume_ratio_gt_1_5": 0.20
    }

    SHORT_WEIGHTS = {
        "relative_strength_lt_1": 0.50,
        "close_lt_ema20": 0.30,
        "volume_ratio_gt_1_5": 0.20
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

            "relative_strength_gt_1":
                float(
                    row["relative_strength"]
                ) > 1.0,

            "close_gt_ema20":
                float(
                    row["c"]
                ) > float(
                    row["ema20"]
                ),

            "volume_ratio_gt_1_5":
                float(
                    row["volume_ratio"]
                ) > 1.5
        }

        short_conditions = {

            "relative_strength_lt_1":
                float(
                    row["relative_strength"]
                ) < 1.0,

            "close_lt_ema20":
                float(
                    row["c"]
                ) < float(
                    row["ema20"]
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
                    "relative_strength",

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
                    "relative_strength",

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
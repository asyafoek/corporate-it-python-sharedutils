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


class GapProvider(
    SignalProvider
):

    LONG_WEIGHTS = {
        "gap_gt_3": 0.40,
        "volume_ratio_gt_2": 0.30,
        "close_gt_open": 0.30
    }

    SHORT_WEIGHTS = {
        "gap_lt_minus_3": 0.40,
        "volume_ratio_gt_2": 0.30,
        "close_lt_open": 0.30
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

            "gap_gt_3":
                float(
                    row["gap_percentage"]
                ) > 3.0,

            "volume_ratio_gt_2":
                float(
                    row["volume_ratio"]
                ) > 2.0,

            "close_gt_open":
                float(
                    row["c"]
                ) > float(
                    row["o"]
                )
        }

        short_conditions = {

            "gap_lt_minus_3":
                float(
                    row["gap_percentage"]
                ) < -3.0,

            "volume_ratio_gt_2":
                float(
                    row["volume_ratio"]
                ) > 2.0,

            "close_lt_open":
                float(
                    row["c"]
                ) < float(
                    row["o"]
                )
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
                    "gap",

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
                    "gap",

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
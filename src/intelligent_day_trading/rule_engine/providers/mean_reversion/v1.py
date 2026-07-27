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


class MeanReversionProvider(
    SignalProvider
):

    LONG_WEIGHTS = {
        "rsi_lt_30": 0.50,
        "distance_from_ema20_gt_3": 0.30,
        "volume_ratio_gt_1": 0.20
    }

    SHORT_WEIGHTS = {
        "rsi_gt_70": 0.50,
        "distance_above_ema20_gt_3": 0.30,
        "volume_ratio_gt_1": 0.20
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

        ema20 = float(
            row["ema20"]
        )

        distance_below_ema20 = (
            (ema20 - close)
            / ema20
        ) * 100

        distance_above_ema20 = (
            (close - ema20)
            / ema20
        ) * 100

        long_conditions = {

            "rsi_lt_30":
                float(
                    row["rsi14"]
                ) < 30.0,

            "distance_from_ema20_gt_3":
                distance_below_ema20 > 3.0,

            "volume_ratio_gt_1":
                float(
                    row["volume_ratio"]
                ) > 1.0
        }

        short_conditions = {

            "rsi_gt_70":
                float(
                    row["rsi14"]
                ) > 70.0,

            "distance_above_ema20_gt_3":
                distance_above_ema20 > 3.0,

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
                    "mean_reversion",

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
                    "mean_reversion",

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
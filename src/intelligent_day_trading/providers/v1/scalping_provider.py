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


class ScalpingProvider(
    SignalProvider
):

    LONG_WEIGHTS = {
        "close_gt_ema8": 0.35,
        "volume_ratio_gt_2": 0.35,
        "rsi_between_50_70": 0.30
    }

    SHORT_WEIGHTS = {
        "close_lt_ema8": 0.35,
        "volume_ratio_gt_2": 0.35,
        "rsi_between_30_50": 0.30
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

            "close_gt_ema8":
                float(
                    row["c"]
                ) > float(
                    row["ema8"]
                ),

            "volume_ratio_gt_2":
                float(
                    row["volume_ratio"]
                ) > 2.0,

            "rsi_between_50_70":
                50.0 <= float(
                    row["rsi14"]
                ) <= 70.0
        }

        short_conditions = {

            "close_lt_ema8":
                float(
                    row["c"]
                ) < float(
                    row["ema8"]
                ),

            "volume_ratio_gt_2":
                float(
                    row["volume_ratio"]
                ) > 2.0,

            "rsi_between_30_50":
                30.0 <= float(
                    row["rsi14"]
                ) <= 50.0
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
                    "scalping",

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
                    "scalping",

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
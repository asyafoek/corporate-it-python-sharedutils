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


class TrendFollowingProvider(
    SignalProvider
):

    LONG_WEIGHTS = {
        "ema20_gt_ema50": 0.30,
        "ema50_gt_ema200": 0.40,
        "close_gt_ema20": 0.30
    }

    SHORT_WEIGHTS = {
        "ema20_lt_ema50": 0.30,
        "ema50_lt_ema200": 0.40,
        "close_lt_ema20": 0.30
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

            "ema20_gt_ema50":
                float(
                    row["ema20"]
                ) > float(
                    row["ema50"]
                ),

            "ema50_gt_ema200":
                float(
                    row["ema50"]
                ) > float(
                    row["ema200"]
                ),

            "close_gt_ema20":
                float(
                    row["c"]
                ) > float(
                    row["ema20"]
                )
        }

        short_conditions = {

            "ema20_lt_ema50":
                float(
                    row["ema20"]
                ) < float(
                    row["ema50"]
                ),

            "ema50_lt_ema200":
                float(
                    row["ema50"]
                ) < float(
                    row["ema200"]
                ),

            "close_lt_ema20":
                float(
                    row["c"]
                ) < float(
                    row["ema20"]
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
                    "trend_following",

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
                    "trend_following",

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
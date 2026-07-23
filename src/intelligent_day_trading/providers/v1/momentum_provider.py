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


class MomentumProvider(
    SignalProvider
):

    LONG_WEIGHTS = {
        "close_gt_ema20": 0.25,
        "ema20_gt_ema50": 0.35,
        "rsi_gt_55": 0.20,
        "volume_ratio_gt_1_5": 0.20
    }

    SHORT_WEIGHTS = {
        "close_lt_ema20": 0.25,
        "ema20_lt_ema50": 0.35,
        "rsi_lt_45": 0.20,
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

        close = float(
            row["c"]
        )

        ema20 = float(
            row["ema20"]
        )

        ema50 = float(
            row["ema50"]
        )

        rsi14 = float(
            row["rsi14"]
        )

        volume_ratio = float(
            row.get(
                "volume_ratio",
                1.0
            )
        )

        long_conditions = {

            "close_gt_ema20":
                close > ema20,

            "ema20_gt_ema50":
                ema20 > ema50,

            "rsi_gt_55":
                rsi14 > 55.0,

            "volume_ratio_gt_1_5":
                volume_ratio > 1.5
        }

        short_conditions = {

            "close_lt_ema20":
                close < ema20,

            "ema20_lt_ema50":
                ema20 < ema50,

            "rsi_lt_45":
                rsi14 < 45.0,

            "volume_ratio_gt_1_5":
                volume_ratio > 1.5
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
                    "momentum",

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
                    "momentum",

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
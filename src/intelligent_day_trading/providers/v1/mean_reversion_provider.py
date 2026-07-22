from intelligent_day_trading.core.confidence import (
    ConfidenceCalculator
)
from intelligent_day_trading.core.constants import (
    SIGNAL_BUY,
    SIDE_LONG
)
from intelligent_day_trading.core.signal_builder import (
    build_signal
)
from intelligent_day_trading.core.signal_provider import (
    SignalProvider
)


class MeanReversionProvider(
    SignalProvider
):

    CONFIDENCE_WEIGHTS = {
        "rsi_lt_30": 0.50,
        "distance_from_ema20_gt_3": 0.30,
        "volume_ratio_gt_1": 0.20
    }

    def evaluate(
        self,
        profile,
        watchlist_entry,
        market_data,
        open_orders,
        reward_risk_ratio
    ):

        row = market_data.iloc[-1]

        close = float(
            row["c"]
        )

        ema20 = float(
            row["ema20"]
        )

        distance_from_ema20 = (
            (ema20 - close)
            / ema20
        ) * 100

        conditions = {

            "rsi_lt_30":
                float(
                    row["rsi14"]
                ) < 30,

            "distance_from_ema20_gt_3":
                distance_from_ema20 > 3,

            "volume_ratio_gt_1":
                float(
                    row["volume_ratio"]
                ) > 1
        }

        confidence = (
            ConfidenceCalculator.calculate(
                conditions,
                self.CONFIDENCE_WEIGHTS
            )
        )

        if not all(
            conditions.values()
        ):
            return []

        return [
            build_signal(
                profile=profile,
                watchlist_entry=watchlist_entry,
                market_data=market_data,
                open_orders=open_orders,
                signal=SIGNAL_BUY,
                side=SIDE_LONG,
                rule_name="mean_reversion",
                reward_risk_ratio=reward_risk_ratio,
                confidence=confidence.confidence,
                evaluation={
                    "reason":
                        "oversold_mean_reversion",

                    "confidence":
                        confidence.confidence,

                    "validations":
                        confidence.validations
                }
            )
        ]
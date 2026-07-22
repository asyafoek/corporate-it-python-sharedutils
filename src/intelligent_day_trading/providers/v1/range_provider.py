from intelligent_day_trading.core.confidence import (
    ConfidenceCalculator
)
from intelligent_day_trading.core.signal_builder import (
    build_signal
)
from intelligent_day_trading.core.signal_provider import (
    SignalProvider
)


class RangeProvider(
    SignalProvider
):

    CONFIDENCE_WEIGHTS = {
        "close_near_low_20": 0.40,
        "rsi_lt_40": 0.30,
        "volume_ratio_gt_1": 0.30
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

        low_20 = float(
            row["low_20"]
        )

        distance = (
            abs(close - low_20)
            / low_20
        )

        conditions = {

            "close_near_low_20":
                distance <= 0.01,

            "rsi_lt_40":
                float(
                    row["rsi14"]
                ) < 40,

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
                signal="buy",
                side="long",
                rule_name="range",
                reward_risk_ratio=reward_risk_ratio,
                confidence=confidence.confidence,
                evaluation={
                    "reason":
                        "range_bounce",

                    "confidence":
                        confidence.confidence,

                    "validations":
                        confidence.validations
                }
            )
        ]
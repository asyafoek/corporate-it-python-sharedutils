from intelligent_day_trading.core.confidence import (
    ConfidenceCalculator
)
from intelligent_day_trading.core.signal_builder import (
    build_signal
)
from intelligent_day_trading.core.signal_provider import (
    SignalProvider
)


class SectorRotationProvider(
    SignalProvider
):

    CONFIDENCE_WEIGHTS = {
        "sector_strength_gt_1": 0.50,
        "relative_strength_gt_1": 0.30,
        "close_gt_ema20": 0.20
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

        conditions = {

            "sector_strength_gt_1":
                row["sector_strength"] > 1,

            "relative_strength_gt_1":
                row["relative_strength"] > 1,

            "close_gt_ema20":
                row["c"] > row["ema20"]
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
                rule_name="sector_rotation",
                reward_risk_ratio=reward_risk_ratio,
                confidence=confidence.confidence,
                evaluation={
                    "reason":
                        "capital_rotation_detected",

                    "confidence":
                        confidence.confidence,

                    "validations":
                        confidence.validations
                }
            )
        ]
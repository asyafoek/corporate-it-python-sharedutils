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


class ReversalProvider(
    SignalProvider
):

    CONFIDENCE_WEIGHTS = {
        "rsi_lt_25": 0.40,
        "close_gt_ema8": 0.30,
        "volume_ratio_gt_1_5": 0.30
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

            "rsi_lt_25":
                float(
                    row["rsi14"]
                ) < 25,

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
                rule_name="reversal",
                reward_risk_ratio=reward_risk_ratio,
                confidence=confidence.confidence,
                evaluation={
                    "reason":
                        "reversal_detected",

                    "confidence":
                        confidence.confidence,

                    "validations":
                        confidence.validations
                }
            )
        ]
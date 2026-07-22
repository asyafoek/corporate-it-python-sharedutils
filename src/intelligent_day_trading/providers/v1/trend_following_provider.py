from intelligent_day_trading.core.confidence import (
    ConfidenceCalculator
)
from intelligent_day_trading.core.signal_builder import (
    build_signal
)
from intelligent_day_trading.core.signal_provider import (
    SignalProvider
)


class TrendFollowingProvider(
    SignalProvider
):

    CONFIDENCE_WEIGHTS = {
        "ema20_gt_ema50": 0.30,
        "ema50_gt_ema200": 0.40,
        "close_gt_ema20": 0.30
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

            "ema20_gt_ema50":
                float(row["ema20"])
                >
                float(row["ema50"]),

            "ema50_gt_ema200":
                float(row["ema50"])
                >
                float(row["ema200"]),

            "close_gt_ema20":
                float(row["c"])
                >
                float(row["ema20"])
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
                rule_name="trend_following",
                reward_risk_ratio=reward_risk_ratio,
                confidence=confidence.confidence,
                evaluation={
                    "reason":
                        "trend_confirmed",

                    "confidence":
                        confidence.confidence,

                    "validations":
                        confidence.validations
                }
            )
        ]

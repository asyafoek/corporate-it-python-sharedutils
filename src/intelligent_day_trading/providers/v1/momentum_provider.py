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


class MomentumProvider(
    SignalProvider
):

    CONFIDENCE_WEIGHTS = {
        "close_gt_ema20": 0.25,
        "ema20_gt_ema50": 0.35,
        "rsi_gt_55": 0.20,
        "volume_ratio_gt_1_5": 0.20
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

        close = float(row["c"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        rsi14 = float(row["rsi14"])

        volume_ratio = float(
            row.get(
                "volume_ratio",
                1.0
            )
        )

        conditions = {

            "close_gt_ema20":
                close > ema20,

            "ema20_gt_ema50":
                ema20 > ema50,

            "rsi_gt_55":
                rsi14 > 55,

            "volume_ratio_gt_1_5":
                volume_ratio > 1.5
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
                rule_name="momentum",
                reward_risk_ratio=reward_risk_ratio,
                confidence=confidence.confidence,
                evaluation={
                    "reason":
                        "all_entry_conditions_passed",

                    "confidence":
                        confidence.confidence,

                    "validations":
                        confidence.validations
                }
            )
        ]
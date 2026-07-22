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


class NewsProvider(
    SignalProvider
):

    CONFIDENCE_WEIGHTS = {
        "news_sentiment_gt_075": 0.50,
        "volume_ratio_gt_2": 0.30,
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

            "news_sentiment_gt_075":
                float(
                    row["news_sentiment"]
                ) > 0.75,

            "volume_ratio_gt_2":
                float(
                    row["volume_ratio"]
                ) > 2.0,

            "close_gt_ema20":
                float(
                    row["c"]
                ) > float(
                    row["ema20"]
                )
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
                rule_name="news",
                reward_risk_ratio=reward_risk_ratio,
                confidence=confidence.confidence,
                evaluation={
                    "reason":
                        "positive_news_momentum",

                    "confidence":
                        confidence.confidence,

                    "validations":
                        confidence.validations
                }
            )
        ]
from intelligent_day_trading.rule_engine.core.confidence import (
    ConfidenceCalculator
)
from intelligent_day_trading.rule_engine.core.constants import (
    SIGNAL_BUY,
    SIGNAL_SELL,
    SIGNAL_WAIT,
    SIDE_LONG,
    SIDE_SHORT
)
from intelligent_day_trading.rule_engine.core.signal_provider import (
    SignalProvider
)


class Provider(
    SignalProvider
):

    LONG_WEIGHTS = {
        "news_sentiment_gt_075": 0.50,
        "rvol_gt_2": 0.30,
        "close_gt_ema20": 0.20
    }

    SHORT_WEIGHTS = {
        "news_sentiment_lt_minus_075": 0.50,
        "rvol_gt_2": 0.30,
        "close_lt_ema20": 0.20
    }

    def evaluate(
        self,
        profile,
        watchlist_entry,
        market_data,
        open_orders
    ):

        row = market_data.iloc[-1]

        news_sentiment = float(
            row["news_sentiment"]
            if row["news_sentiment"] is not None
            else 0
        )

        horizon = profile[
            "strategy_trading_horizon"
        ]

        if horizon.lower() == "intraday":

            long_conditions = {

                "news_sentiment_gt_075":
                    news_sentiment > 0.75,

                "rvol_gt_2":
                    float(
                        row["rvol"]
                    ) > 2.0,

                "close_gt_ema20":
                    float(
                        row["c"]
                    ) > float(
                        row["ema20"]
                    )
            }

            short_conditions = {

                "news_sentiment_lt_minus_075":
                    news_sentiment < -0.75,

                "rvol_gt_2":
                    float(
                        row["rvol"]
                    ) > 2.0,

                "close_lt_ema20":
                    float(
                        row["c"]
                    ) < float(
                        row["ema20"]
                    )
            }

        elif horizon.lower() == "swing":

            long_conditions = {

                "news_sentiment_gt_075":
                    news_sentiment > 0.50,

                "rvol_gt_2":
                    float(
                        row["rvol"]
                    ) > 1.5,

                "close_gt_ema20":
                    float(
                        row["c"]
                    ) > float(
                        row["ema20"]
                    )
            }

            short_conditions = {

                "news_sentiment_lt_minus_075":
                    news_sentiment < -0.50,

                "rvol_gt_2":
                    float(
                        row["rvol"]
                    ) > 1.5,

                "close_lt_ema20":
                    float(
                        row["c"]
                    ) < float(
                        row["ema20"]
                    )
            }

        elif horizon.lower() == "position":

            long_conditions = {

                "news_sentiment_gt_075":
                    news_sentiment > 0.25,

                "rvol_gt_2":
                    float(
                        row["rvol"]
                    ) > 1.0,

                "close_gt_ema20":
                    float(
                        row["c"]
                    ) > float(
                        row["ema20"]
                    )
            }

            short_conditions = {

                "news_sentiment_lt_minus_075":
                    news_sentiment < -0.25,

                "rvol_gt_2":
                    float(
                        row["rvol"]
                    ) > 1.0,

                "close_lt_ema20":
                    float(
                        row["c"]
                    ) < float(
                        row["ema20"]
                    )
            }

        else:

            raise ValueError(
                f"Unsupported trading horizon: "
                f"{horizon}"
            )

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
                "engine_version":
                    self.engine_version,

                "provider":
                    self.provider_name,

                "provider_version":
                    self.provider_version,

                "side":
                    SIDE_LONG,

                "signal":
                    SIGNAL_BUY
                    if all(
                        long_conditions.values()
                    )
                    else SIGNAL_WAIT,

                "confidence_percentage":
                    round(
                        sum(
                            validation[
                                "contribution"
                            ]
                            for validation
                            in long_confidence.validations
                        ) * 100,
                        2
                    ),

                "validations":
                    long_confidence.validations
            })

        if any(
            short_conditions.values()
        ):

            results.append({
                "engine_version":
                    self.engine_version,

                "provider":
                    self.provider_name,

                "provider_version":
                    self.provider_version,

                "side":
                    SIDE_SHORT,

                "signal":
                    SIGNAL_SELL
                    if all(
                        short_conditions.values()
                    )
                    else SIGNAL_WAIT,

                "confidence_percentage":
                    round(
                        sum(
                            validation[
                                "contribution"
                            ]
                            for validation
                            in short_confidence.validations
                        ) * 100,
                        2
                    ),

                "validations":
                    short_confidence.validations
            })

        return results
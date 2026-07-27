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

        horizon = profile[
            "strategy_trading_horizon"
        ]

        if horizon == "intraday":

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

        elif horizon == "swing":

            long_conditions = {

                "ema20_gt_ema50":
                    (
                        float(
                            row["ema20"]
                        ) / float(
                            row["ema50"]
                        )
                    ) > 1.01,

                "ema50_gt_ema200":
                    (
                        float(
                            row["ema50"]
                        ) / float(
                            row["ema200"]
                        )
                    ) > 1.01,

                "close_gt_ema20":
                    float(
                        row["c"]
                    ) > float(
                        row["ema20"]
                    )
            }

            short_conditions = {

                "ema20_lt_ema50":
                    (
                        float(
                            row["ema20"]
                        ) / float(
                            row["ema50"]
                        )
                    ) < 0.99,

                "ema50_lt_ema200":
                    (
                        float(
                            row["ema50"]
                        ) / float(
                            row["ema200"]
                        )
                    ) < 0.99,

                "close_lt_ema20":
                    float(
                        row["c"]
                    ) < float(
                        row["ema20"]
                    )
            }

        elif horizon == "position":

            long_conditions = {

                "ema20_gt_ema50":
                    (
                        float(
                            row["ema20"]
                        ) / float(
                            row["ema50"]
                        )
                    ) > 1.03,

                "ema50_gt_ema200":
                    (
                        float(
                            row["ema50"]
                        ) / float(
                            row["ema200"]
                        )
                    ) > 1.03,

                "close_gt_ema20":
                    float(
                        row["c"]
                    ) > float(
                        row["ema20"]
                    )
            }

            short_conditions = {

                "ema20_lt_ema50":
                    (
                        float(
                            row["ema20"]
                        ) / float(
                            row["ema50"]
                        )
                    ) < 0.97,

                "ema50_lt_ema200":
                    (
                        float(
                            row["ema50"]
                        ) / float(
                            row["ema200"]
                        )
                    ) < 0.97,

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

                "validations":
                    short_confidence.validations
            })

        return results
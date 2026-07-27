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
        "close_gt_high_20": 0.50,
        "volume_ratio_gt_2": 0.30,
        "rsi_gt_60": 0.20
    }

    SHORT_WEIGHTS = {
        "close_lt_low_20": 0.50,
        "volume_ratio_gt_2": 0.30,
        "rsi_lt_40": 0.20
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

                "close_gt_high_20":
                    float(
                        row["c"]
                    ) > float(
                        row["high_20"]
                    ),

                "volume_ratio_gt_2":
                    float(
                        row["volume_ratio"]
                    ) > 2.0,

                "rsi_gt_60":
                    float(
                        row["rsi14"]
                    ) > 60.0
            }

            short_conditions = {

                "close_lt_low_20":
                    float(
                        row["c"]
                    ) < float(
                        row["low_20"]
                    ),

                "volume_ratio_gt_2":
                    float(
                        row["volume_ratio"]
                    ) > 2.0,

                "rsi_lt_40":
                    float(
                        row["rsi14"]
                    ) < 40.0
            }

        elif horizon == "swing":

            long_conditions = {

                "close_gt_high_20":
                    float(
                        row["c"]
                    ) > float(
                        row["high_20"]
                    ),

                "volume_ratio_gt_2":
                    float(
                        row["volume_ratio"]
                    ) > 1.5,

                "rsi_gt_60":
                    float(
                        row["rsi14"]
                    ) > 55.0
            }

            short_conditions = {

                "close_lt_low_20":
                    float(
                        row["c"]
                    ) < float(
                        row["low_20"]
                    ),

                "volume_ratio_gt_2":
                    float(
                        row["volume_ratio"]
                    ) > 1.5,

                "rsi_lt_40":
                    float(
                        row["rsi14"]
                    ) < 45.0
            }

        elif horizon == "position":

            long_conditions = {

                "close_gt_high_20":
                    float(
                        row["c"]
                    ) > float(
                        row["high_20"]
                    ),

                "volume_ratio_gt_2":
                    float(
                        row["volume_ratio"]
                    ) > 1.0,

                "rsi_gt_60":
                    float(
                        row["rsi14"]
                    ) > 50.0
            }

            short_conditions = {

                "close_lt_low_20":
                    float(
                        row["c"]
                    ) < float(
                        row["low_20"]
                    ),

                "volume_ratio_gt_2":
                    float(
                        row["volume_ratio"]
                    ) > 1.0,

                "rsi_lt_40":
                    float(
                        row["rsi14"]
                    ) < 50.0
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
                            in long_confidence.validations
                        ) * 100,
                        2
                    ),


                "validations":
                    short_confidence.validations
            })

        return results
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
        "close_gt_ema8": 0.35,
        "rvol_gt_2": 0.35,
        "rsi_between_50_70": 0.30
    }

    SHORT_WEIGHTS = {
        "close_lt_ema8": 0.35,
        "rvol_gt_2": 0.35,
        "rsi_between_30_50": 0.30
    }

    def evaluate(
        self,
        profile,
        watchlist_entry,
        market_data,
        open_orders
    ):

        row = market_data.iloc[-1]

        if any(
            row.get(col) is None
            for col in [
                "c",
                "ema8",
                "rvol",
                "rsi_14"
            ]
        ):
            return []

        horizon = profile[
            "strategy_trading_horizon"
        ]

        if horizon.lower() == "intraday":

            long_conditions = {

                "close_gt_ema8":
                    float(
                        row["c"]
                    ) > float(
                        row["ema8"]
                    ),

                "rvol_gt_2":
                    float(
                        row["rvol"]
                    ) > 2.0,

                "rsi_between_50_70":
                    50.0 <= float(
                        row["rsi_14"]
                    ) <= 70.0
            }

            short_conditions = {

                "close_lt_ema8":
                    float(
                        row["c"]
                    ) < float(
                        row["ema8"]
                    ),

                "rvol_gt_2":
                    float(
                        row["rvol"]
                    ) > 2.0,

                "rsi_between_30_50":
                    30.0 <= float(
                        row["rsi_14"]
                    ) <= 50.0
            }

        elif horizon.lower() == "swing":

            long_conditions = {

                "close_gt_ema8":
                    float(
                        row["c"]
                    ) > float(
                        row["ema8"]
                    ),

                "rvol_gt_2":
                    float(
                        row["rvol"]
                    ) > 1.5,

                "rsi_between_50_70":
                    45.0 <= float(
                        row["rsi_14"]
                    ) <= 75.0
            }

            short_conditions = {

                "close_lt_ema8":
                    float(
                        row["c"]
                    ) < float(
                        row["ema8"]
                    ),

                "rvol_gt_2":
                    float(
                        row["rvol"]
                    ) > 1.5,

                "rsi_between_30_50":
                    25.0 <= float(
                        row["rsi_14"]
                    ) <= 55.0
            }

        elif horizon.lower() == "position":

            long_conditions = {

                "close_gt_ema8":
                    float(
                        row["c"]
                    ) > float(
                        row["ema8"]
                    ),

                "rvol_gt_2":
                    float(
                        row["rvol"]
                    ) > 1.0,

                "rsi_between_50_70":
                    40.0 <= float(
                        row["rsi_14"]
                    ) <= 80.0
            }

            short_conditions = {

                "close_lt_ema8":
                    float(
                        row["c"]
                    ) < float(
                        row["ema8"]
                    ),

                "rvol_gt_2":
                    float(
                        row["rvol"]
                    ) > 1.0,

                "rsi_between_30_50":
                    20.0 <= float(
                        row["rsi_14"]
                    ) <= 60.0
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
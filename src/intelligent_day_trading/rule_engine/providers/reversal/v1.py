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
        "rsi_lt_25": 0.40,
        "close_gt_ema8": 0.30,
        "rvol_gt_1_5": 0.30
    }

    SHORT_WEIGHTS = {
        "rsi_gt_75": 0.40,
        "close_lt_ema8": 0.30,
        "rvol_gt_1_5": 0.30
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
                "rsi_14",
                "c",
                "ema8",
                "rvol"
            ]
        ):
            return []

        rvol = float(
            row["rvol"]
            if row["rvol"] is not None
            else 1.0
        )

        horizon = profile[
            "strategy_trading_horizon"
        ]

        if horizon.lower() == "intraday":

            long_conditions = {

                "rsi_lt_25":
                    float(
                        row["rsi_14"]
                    ) < 25.0,

                "close_gt_ema8":
                    float(
                        row["c"]
                    ) > float(
                        row["ema8"]
                    ),

                "rvol_gt_1_5":
                    float(
                        row["rvol"]
                    ) > 1.5
            }

            short_conditions = {

                "rsi_gt_75":
                    float(
                        row["rsi_14"]
                    ) > 75.0,

                "close_lt_ema8":
                    float(
                        row["c"]
                    ) < float(
                        row["ema8"]
                    ),

                "rvol_gt_1_5":
                    float(
                        row["rvol"]
                    ) > 1.5
            }

        elif horizon.lower() == "swing":

            long_conditions = {

                "rsi_lt_25":
                    float(
                        row["rsi_14"]
                    ) < 30.0,

                "close_gt_ema8":
                    float(
                        row["c"]
                    ) > float(
                        row["ema8"]
                    ),

                "rvol_gt_1_5":
                    float(
                        row["rvol"]
                    ) > 1.2
            }

            short_conditions = {

                "rsi_gt_75":
                    float(
                        row["rsi_14"]
                    ) > 70.0,

                "close_lt_ema8":
                    float(
                        row["c"]
                    ) < float(
                        row["ema8"]
                    ),

                "rvol_gt_1_5":
                    float(
                        row["rvol"]
                    ) > 1.2
            }

        elif horizon.lower() == "position":

            long_conditions = {

                "rsi_lt_25":
                    float(
                        row["rsi_14"]
                    ) < 35.0,

                "close_gt_ema8":
                    float(
                        row["c"]
                    ) > float(
                        row["ema8"]
                    ),

                "rvol_gt_1_5":
                    float(
                        row["rvol"]
                    ) > 1.0
            }

            short_conditions = {

                "rsi_gt_75":
                    float(
                        row["rsi_14"]
                    ) > 65.0,

                "close_lt_ema8":
                    float(
                        row["c"]
                    ) < float(
                        row["ema8"]
                    ),

                "rvol_gt_1_5":
                    float(
                        row["rvol"]
                    ) > 1.0
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
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
        "close_gt_ema20": 0.25,
        "ema20_gt_ema50": 0.35,
        "rsi_gt_55": 0.20,
        "rvol_gt_1_5": 0.20
    }

    SHORT_WEIGHTS = {
        "close_lt_ema20": 0.25,
        "ema20_lt_ema50": 0.35,
        "rsi_lt_45": 0.20,
        "rvol_gt_1_5": 0.20
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
                "ema20",
                "ema50",
                "rsi_14"
            ]
        ):
            return []

        rvol = float(
            row["rvol"]
            if row["rvol"] is not None
            else 1.0
        )

        close = float(
            row["c"]
        )

        ema20 = float(
            row["ema20"]
        )

        ema50 = float(
            row["ema50"]
        )

        rsi_14 = float(
            row["rsi_14"]
        )

        rvol = float(
            row.get(
                "rvol",
                1.0
            )
        )

        horizon = profile[
            "strategy_trading_horizon"
        ]

        if horizon.lower() == "intraday":

            long_conditions = {

                "close_gt_ema20":
                    close > ema20,

                "ema20_gt_ema50":
                    ema20 > ema50,

                "rsi_gt_55":
                    rsi_14 > 55.0,

                "rvol_gt_1_5":
                    rvol > 1.5
            }

            short_conditions = {

                "close_lt_ema20":
                    close < ema20,

                "ema20_lt_ema50":
                    ema20 < ema50,

                "rsi_lt_45":
                    rsi_14 < 45.0,

                "rvol_gt_1_5":
                    rvol > 1.5
            }

        elif horizon.lower() == "swing":

            long_conditions = {

                "close_gt_ema20":
                    close > ema20,

                "ema20_gt_ema50":
                    ema20 > ema50,

                "rsi_gt_55":
                    rsi_14 > 50.0,

                "rvol_gt_1_5":
                    rvol > 1.2
            }

            short_conditions = {

                "close_lt_ema20":
                    close < ema20,

                "ema20_lt_ema50":
                    ema20 < ema50,

                "rsi_lt_45":
                    rsi_14 < 50.0,

                "rvol_gt_1_5":
                    rvol > 1.2
            }

        elif horizon.lower() == "position":

            long_conditions = {

                "close_gt_ema20":
                    close > ema20,

                "ema20_gt_ema50":
                    ema20 > ema50,

                "rsi_gt_55":
                    rsi_14 > 50.0,

                "rvol_gt_1_5":
                    rvol > 1.0
            }

            short_conditions = {

                "close_lt_ema20":
                    close < ema20,

                "ema20_lt_ema50":
                    ema20 < ema50,

                "rsi_lt_45":
                    rsi_14 < 50.0,

                "rvol_gt_1_5":
                    rvol > 1.0
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
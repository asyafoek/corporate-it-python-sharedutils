import time
import uuid

import pandas as pd

from intelligent_day_trading.engines.v1.provider_configurations import (
    PROVIDER_CONFIGURATIONS
)

from intelligent_day_trading.core.constants import (
    TRADING_STATE_DISABLED
)

from intelligent_day_trading.providers.v1.momentum_provider import (
    MomentumProvider
)
from intelligent_day_trading.providers.v1.breakout_provider import (
    BreakoutProvider
)
from intelligent_day_trading.providers.v1.trend_following_provider import (
    TrendFollowingProvider
)
from intelligent_day_trading.providers.v1.mean_reversion_provider import (
    MeanReversionProvider
)
from intelligent_day_trading.providers.v1.reversal_provider import (
    ReversalProvider
)
from intelligent_day_trading.providers.v1.scalping_provider import (
    ScalpingProvider
)
from intelligent_day_trading.providers.v1.volatility_provider import (
    VolatilityProvider
)
from intelligent_day_trading.providers.v1.news_provider import (
    NewsProvider
)
from intelligent_day_trading.providers.v1.gap_provider import (
    GapProvider
)
from intelligent_day_trading.providers.v1.range_provider import (
    RangeProvider
)
from intelligent_day_trading.providers.v1.sector_rotation_provider import (
    SectorRotationProvider
)
from intelligent_day_trading.providers.v1.relative_strength_provider import (
    RelativeStrengthProvider
)


class TradingRuleEngineV1:

    MINIMUM_CONSENSUS_PERCENTAGE = 60.0

    PROVIDERS = {

        "momentum":
            MomentumProvider(),

        "breakout":
            BreakoutProvider(),

        "trend_following":
            TrendFollowingProvider(),

        "mean_reversion":
            MeanReversionProvider(),

        "reversal":
            ReversalProvider(),

        "scalping":
            ScalpingProvider(),

        "volatility":
            VolatilityProvider(),

        "news":
            NewsProvider(),

        "gap":
            GapProvider(),

        "range":
            RangeProvider(),

        "sector_rotation":
            SectorRotationProvider(),

        "relative_strength":
            RelativeStrengthProvider()
    }

    @staticmethod
    def _reward_risk_ratio(
        profile: dict,
        market_regime: str
    ) -> float:

        mapping = {

            "bullish_quiet":
                profile.get(
                    "strategy_reward_risk_notation_bullish_quiet",
                    "0:0"
                ),

            "bullish_volatile":
                profile.get(
                    "strategy_reward_risk_notation_bullish_volatile",
                    "0:0"
                ),

            "sideways_quiet":
                profile.get(
                    "strategy_reward_risk_notation_sideways_quiet",
                    "0:0"
                ),

            "sideways_volatile":
                profile.get(
                    "strategy_reward_risk_notation_sideways_volatile",
                    "0:0"
                ),

            "bearish_quiet":
                profile.get(
                    "strategy_reward_risk_notation_bearish_quiet",
                    "0:0"
                ),

            "bearish_volatile":
                profile.get(
                    "strategy_reward_risk_notation_bearish_volatile",
                    "0:0"
                )
        }

        notation = mapping.get(
            market_regime,
            "0:0"
        )

        try:

            return float(
                notation.split(":")[0]
            )

        except Exception:

            return 0.0

    @staticmethod
    def _market_timestamp(
        market_data: pd.DataFrame
    ) -> int:

        row = (
            market_data.iloc[-1]
        )

        if "e" in row:

            try:

                return int(
                    row["e"]
                )

            except Exception:
                pass

        return int(
            market_data.index[-1]
            .timestamp()
            * 1000
        )

    @staticmethod
    def _calculate_consensus(
        provider_results: list,
        expected_signal: str
    ) -> float:

        if not provider_results:
            return 0.0

        total_weight = sum(

            float(
                result.get(
                    "weight",
                    0
                )
            )

            for result in (
                provider_results
            )
        )

        if total_weight <= 0:
            return 0.0

        matching_weight = sum(

            float(
                result.get(
                    "weight",
                    0
                )
            )

            for result in (
                provider_results
            )

            if result.get(
                "signal"
            ) == expected_signal
        )

        return round(

            (
                matching_weight
                /
                total_weight
            ) * 100,

            2
        )
    
    def _apply_position_management_override(
        self,
        profile: dict,
        watchlist_entry: dict,
        market_data: pd.DataFrame,
        open_orders: pd.DataFrame,
    ) -> dict:

        if open_orders.empty:

            return {

                "override_applied": False,

                "override_reason": None,

                "override_signal": None,

                "override_orders": None
            }

        ticker = watchlist_entry.get(
            "ticker"
        )

        ticker_orders = open_orders.loc[

            (
                open_orders["ticker"]
                ==
                ticker
            )

            &

            (
                open_orders["status"]
                ==
                "open"
            )
        ]

        if ticker_orders.empty:

            return {

                "override_applied": False,

                "override_reason": None,

                "override_signal": None,

                "override_orders": None
            }

        current_price = float(
            market_data.iloc[-1]["c"]
        )

        take_profit_percentage = float(

            profile.get(
                "strategy_position_management_take_profit_percentage",
                0
            )
        )

        stop_loss_percentage = float(

            profile.get(
                "strategy_position_management_stop_losing_percentage",
                0
            )
        )

        take_profit_orders = []

        stop_loss_orders = []

        for _, order in (
            ticker_orders.iterrows()
        ):

            entry_price = float(
                order["entry_price"]
            )

            order_side = str(
                order["side"]
            ).lower()

            order_id = order["order_id"]

            if order_side == "long":

                take_profit_price = (

                    entry_price

                    *

                    (
                        1
                        +
                        (
                            take_profit_percentage
                            / 100
                        )
                    )
                )

                stop_loss_price = (

                    entry_price

                    *

                    (
                        1
                        -
                        (
                            stop_loss_percentage
                            / 100
                        )
                    )
                )

                if current_price >= take_profit_price:

                    take_profit_orders.append(
                        order_id
                    )

                if current_price <= stop_loss_price:

                    stop_loss_orders.append(
                        order_id
                    )

            elif order_side == "short":

                take_profit_price = (

                    entry_price

                    *

                    (
                        1
                        -
                        (
                            take_profit_percentage
                            / 100
                        )
                    )
                )

                stop_loss_price = (

                    entry_price

                    *

                    (
                        1
                        +
                        (
                            stop_loss_percentage
                            / 100
                        )
                    )
                )

                if current_price <= take_profit_price:

                    take_profit_orders.append(
                        order_id
                    )

                if current_price >= stop_loss_price:

                    stop_loss_orders.append(
                        order_id
                    )

        if take_profit_orders:

            return {

                "override_applied": True,

                "override_reason":
                    "take_profit_reached",

                "override_signal":
                    "sell",

                "override_orders":
                    take_profit_orders
            }

        if stop_loss_orders:

            return {

                "override_applied": True,

                "override_reason":
                    "stop_loss_triggered",

                "override_signal":
                    "sell",

                "override_orders":
                    stop_loss_orders
            }

        max_trades_per_ticker = int(

            profile.get(
                "strategy_position_management_max_trades_per_ticker",
                1
            )
        )

        open_trade_count = len(
            ticker_orders
        )

        if (
            open_trade_count
            <
            max_trades_per_ticker
        ):

            return {

                "override_applied": False,

                "override_reason": None,

                "override_signal": None,

                "override_orders": None
            }


        return {

            "override_applied": True,

            "override_reason":
                "max_trades_per_ticker_reached",

            "override_signal":
                "hold",

            "override_orders":
                ticker_orders[
                    "order_id"
                ].tolist()
        }

    def _build_signal(
        self,
        profile: dict,
        watchlist_entry: dict,
        market_data: pd.DataFrame,
        open_orders: pd.DataFrame,
        signal: str,
        side: str,
        reward_risk_ratio: float,
        consensus_percentage: float,
        provider_results: list,
        reason: str,
        provider_consensus_signal: str,
        override_applied: bool,
        override_reason: str | None,
        override_signal: str | None,
        override_orders: list | None

    ) -> dict:            

        market_snapshot = (
            market_data.iloc[-1]
            .to_dict()
        )

        return {

            "signal_id":
                str(
                    uuid.uuid4()
                ),

            "run_id":
                watchlist_entry.get(
                    "run_id"
                ),

            "signal":
                signal,

            "side":
                side,

            "reward_risk_ratio":
                reward_risk_ratio,

            "consensus_percentage":
                consensus_percentage,

            "market_timestamp":
                self._market_timestamp(
                    market_data
                ),

            "signal_generated_at":
                int(
                    time.time()
                    * 1000
                ),

            "market_snapshot":
                market_snapshot,

            "profile_snapshot":
                dict(profile),

            "watchlist_entry_snapshot":
                dict(
                    watchlist_entry
                ),

            "open_orders_snapshot":
                open_orders.to_dict(
                    orient="records"
                ),


            "evaluation": {

                "reason":
                    reason,

                "provider_consensus_signal":
                    provider_consensus_signal,

                "provider_consensus_percentage":
                    consensus_percentage,

                "override_applied":
                    override_applied,

                "override_reason":
                    override_reason,

                "override_signal":
                    override_signal,

                "override_orders":
                    override_orders,

                "provider_results":
                    provider_results
            }            
        }

    def evaluate(
        self,
        profile: dict,
        watchlist_entry: dict,
        market_data: pd.DataFrame,
        open_orders: pd.DataFrame
    ) -> dict:

        if market_data.empty:

            return {
                "trading_signals": []
            }

        trading_state = (

            profile.get(
                "strategy_trading_state",
                ""
            )
            .lower()
        )

        if (
            trading_state
            ==
            TRADING_STATE_DISABLED
        ):

            return {
                "trading_signals": []
            }

        market_regime = (

            watchlist_entry.get(
                "market_regime",
                ""
            )
            .lower()
        )

        reward_risk_ratio = (

            self._reward_risk_ratio(
                profile,
                market_regime
            )
        )

        if reward_risk_ratio <= 0:

            return {
                "trading_signals": []
            }

        engine_version = (

            profile.get(
                "strategy_regime_rule_version",
                1
            )
        )

        trading_horizon = (

            profile.get(
                "strategy_trading_horizon",
                "intraday"
            )
            .lower()
        )

        configurations = (

            PROVIDER_CONFIGURATIONS.loc[

                (
                    PROVIDER_CONFIGURATIONS[
                        "engine_version"
                    ]
                    ==
                    engine_version
                )

                &

                (
                    PROVIDER_CONFIGURATIONS[
                        "trading_horizon"
                    ]
                    ==
                    trading_horizon
                )

                &

                (
                    PROVIDER_CONFIGURATIONS[
                        "market_regime"
                    ]
                    ==
                    market_regime
                )
            ]
        )

        all_provider_results = []

        for _, configuration in (
            configurations.iterrows()
        ):

            provider_name = (
                configuration[
                    "provider"
                ]
            )

            provider_weight = float(
                configuration[
                    "weight"
                ]
            )

            provider = (
                self.PROVIDERS.get(
                    provider_name
                )
            )

            if provider is None:
                continue

            provider_results = (

                provider.evaluate(
                    profile=profile,
                    watchlist_entry=watchlist_entry,
                    market_data=market_data,
                    open_orders=open_orders
                )
            )

            for provider_result in (
                provider_results
            ):

                provider_result = dict(
                    provider_result
                )

                provider_result[
                    "weight"
                ] = provider_weight

                all_provider_results.append(
                    provider_result
                )

        trading_signals = []

        #
        # LONG CONSENSUS
        #

        long_provider_results = [

            result

            for result in (
                all_provider_results
            )

            if result.get(
                "side"
            ) == "long"
        ]

        if long_provider_results:

            long_consensus = (

                self._calculate_consensus(
                    long_provider_results,
                    "buy"
                )
            )

            if (

                long_consensus
                >=
                self.MINIMUM_CONSENSUS_PERCENTAGE

            ):

                override = (
                    self._apply_position_management_override(
                        profile=profile,
                        watchlist_entry=watchlist_entry,
                        market_data=market_data,
                        open_orders=open_orders,
                    )
                )

                final_signal = (

                    override["override_signal"]

                    if override["override_applied"]

                    else

                    "buy"
                )

                trading_signals.append(

                    self._build_signal(
                        profile=profile,
                        watchlist_entry=watchlist_entry,
                        market_data=market_data,
                        open_orders=open_orders,
                        signal=final_signal,
                        side="long",
                        reward_risk_ratio=reward_risk_ratio,
                        consensus_percentage=long_consensus,
                        provider_results=long_provider_results,
                        reason=(
                            "position_management_override"
                            if override["override_applied"]
                            else "provider_consensus"
                        ),
                        provider_consensus_signal="buy",
                        override_applied=override["override_applied"],
                        override_reason=override["override_reason"],
                        override_signal=override["override_signal"],
                        override_orders=override["override_orders"]
                    )
                )

        #
        # SHORT CONSENSUS
        #

        short_provider_results = [

            result

            for result in (
                all_provider_results
            )

            if result.get(
                "side"
            ) == "short"
        ]

        if short_provider_results:

            short_consensus = (

                self._calculate_consensus(
                    short_provider_results,
                    "sell"
                )
            )

            if (

                short_consensus
                >=
                self.MINIMUM_CONSENSUS_PERCENTAGE

            ):


                override = (
                    self._apply_position_management_override(
                        profile=profile,
                        watchlist_entry=watchlist_entry,
                        market_data=market_data,
                        open_orders=open_orders,
                    )
                )

                final_signal = (

                    override["override_signal"]

                    if override["override_applied"]

                    else

                    "sell"
                )

                trading_signals.append(

                    self._build_signal(
                        profile=profile,
                        watchlist_entry=watchlist_entry,
                        market_data=market_data,
                        open_orders=open_orders,
                        signal=final_signal,
                        side="short",
                        reward_risk_ratio=reward_risk_ratio,
                        consensus_percentage=short_consensus,
                        provider_results=short_provider_results,
                        reason=(
                            "position_management_override"
                            if override["override_applied"]
                            else "provider_consensus"
                        ),
                        provider_consensus_signal="sell",
                        override_applied=override["override_applied"],
                        override_reason=override["override_reason"],
                        override_signal=override["override_signal"],
                        override_orders=override["override_orders"]
                    )
                )

        return {

            "trading_signals":
                trading_signals
        }
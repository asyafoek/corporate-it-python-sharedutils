import pandas as pd

from intelligent_day_trading.core.constants import (
    SIGNAL_COLUMNS,
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
                profile[
                    "strategy_reward_risk_notation_bullish_quiet"
                ],

            "bullish_volatile":
                profile[
                    "strategy_reward_risk_notation_bullish_volatile"
                ],

            "sideways_quiet":
                profile[
                    "strategy_reward_risk_notation_sideways_quiet"
                ],

            "sideways_volatile":
                profile[
                    "strategy_reward_risk_notation_sideways_volatile"
                ],

            "bearish_quiet":
                profile[
                    "strategy_reward_risk_notation_bearish_quiet"
                ],

            "bearish_volatile":
                profile[
                    "strategy_reward_risk_notation_bearish_volatile"
                ]
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

    def evaluate(
        self,
        profile: dict,
        watchlist_entry: dict,
        market_data: pd.DataFrame,
        open_orders: pd.DataFrame
    ) -> pd.DataFrame:

        if market_data.empty:
            return pd.DataFrame(
                columns=SIGNAL_COLUMNS
            )

        trading_state = (
            profile[
                "strategy_trading_state"
            ]
            .lower()
        )

        if trading_state == TRADING_STATE_DISABLED:
            return pd.DataFrame(
                columns=SIGNAL_COLUMNS
            )

        market_regime = (
            watchlist_entry[
                "market_regime"
            ]
            .lower()
        )

        reward_risk_ratio = (
            self._reward_risk_ratio(
                profile,
                market_regime
            )
        )

        #
        # Niet-tradebaar regime
        #
        if reward_risk_ratio <= 0:
            return pd.DataFrame(
                columns=SIGNAL_COLUMNS
            )

        trading_style = (
            profile[
                "strategy_trading_style"
            ]
            .lower()
        )

        provider = (
            self.PROVIDERS.get(
                trading_style
            )
        )

        if provider is None:

            raise ValueError(
                f"Unsupported trading style: "
                f"{trading_style}"
            )

        signals = provider.evaluate(
            profile=profile,
            watchlist_entry=watchlist_entry,
            market_data=market_data,
            open_orders=open_orders,
            reward_risk_ratio=reward_risk_ratio
        )

        return pd.DataFrame(
            signals,
            columns=SIGNAL_COLUMNS
        )
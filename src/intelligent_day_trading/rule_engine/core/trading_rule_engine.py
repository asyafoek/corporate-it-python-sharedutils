
from intelligent_day_trading.rule_engine.core.provider_loader import (
    load_provider
)

from intelligent_day_trading.rule_engine.engine_configs import (
    ENGINE_CONFIGS
)


class TradingRuleEngine:

    def __init__(
        self,
        version: int
    ):

        self.version = version

        self.providers = []

        configuration = (
            ENGINE_CONFIGS.get(
                version
            )
        )

        if configuration is None:

            raise ValueError(
                f"Unsupported engine version: "
                f"{version}"
            )

        for (
            provider_name,
            provider_version
        ) in configuration:

            self.providers.append(

                load_provider(
                    provider_name,
                    provider_version
                )

            )

    def evaluate(
        self,
        profile,
        watchlist_entry,
        market_data,
        open_orders
    ):

        trading_signals = []

        for provider in self.providers:

            provider_results = (

                provider.evaluate(
                    profile,
                    watchlist_entry,
                    market_data,
                    open_orders
                )

            )

            if provider_results:

                trading_signals.extend(
                    provider_results
                )

        return {

            "trading_signals":
                trading_signals

        }
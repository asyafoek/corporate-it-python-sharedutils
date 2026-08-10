from intelligent_day_trading.rule_engine.core.trading_rule_engine import (
    TradingRuleEngine
)


class TradingRuleEngineFactory:

    @classmethod
    def create(
        cls,
        version: int,
        configuration=None
    ):

        return TradingRuleEngine(
            version=version,
            configuration=configuration
        )
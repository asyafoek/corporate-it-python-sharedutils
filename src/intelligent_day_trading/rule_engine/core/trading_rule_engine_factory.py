from intelligent_day_trading.rule_engine.core.trading_rule_engine import (
    TradingRuleEngine
)


class TradingRuleEngineFactory:

    @classmethod
    def create(
        cls,
        version: int
    ):

        return TradingRuleEngine(
            version=version
        )
from intelligent_day_trading.engines.v1.trading_rule_engine import (
    TradingRuleEngineV1
)


class TradingRuleEngineFactory:

    ENGINES = {
        1: TradingRuleEngineV1
    }

    @classmethod
    def create(
        cls,
        version: int
    ):

        engine_class = (
            cls.ENGINES.get(
                version
            )
        )

        if engine_class is None:

            raise ValueError(
                f"Unsupported engine version: "
                f"{version}"
            )

        return engine_class()
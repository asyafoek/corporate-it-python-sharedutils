from copy import deepcopy
from datetime import datetime, UTC
from uuid import uuid4
import json


class TradeFlowBuilder:

    @staticmethod
    def now():
        return datetime.now(UTC).isoformat()

    @staticmethod
    def initialize(
        market_data: dict,
        market: str,
        trading_mode: str
    ) -> dict:

        trade = deepcopy(market_data)

        trade["market"] = market
        trade["trading_mode"] = trading_mode

        return trade

    @staticmethod
    def add_context(
        trade: dict,
        run_id: str,
        trading_horizon: str,
        market_regime: str,
        profile_identity: str,
        profile_name: str,
        side: str,
        rule_engine_version: int = 1
    ) -> dict:

        trade["dataflow"] = {
            "context": {
                "run_id": run_id,
                "external_reference_id": str(uuid4()),
                "trading_horizon": trading_horizon,
                "market_regime": market_regime,
                "profile": {
                    "profile_identity": profile_identity,
                    "profile_name": profile_name,
                    "rule_engine_version": rule_engine_version,
                    "side": side
                }
            },
            "steps": []
        }

        return trade

    @staticmethod
    def add_step(
        trade: dict,
        name: str,
        payload: dict,
        timestamp: str | None = None
    ) -> dict:

        trade["dataflow"]["steps"].append({
            "name": name,
            "timestamp": timestamp or TradeFlowBuilder.now(),
            "payload": payload
        })

        return trade

    @staticmethod
    def add_opportunity_detected(
        trade: dict,
        opportunity_detected: bool,
        added_in_cache: str
    ) -> dict:

        return TradeFlowBuilder.add_step(
            trade=trade,
            name="opportunity_detected",
            payload={
                "opportunity": {
                    "opportunity_detected": opportunity_detected,
                    "added_in_cache": added_in_cache
                }
            }
        )

    @staticmethod
    def add_signal_evaluated(
        trade: dict,
        action: str,
        percentage: float,
        provider_count_configured: int,
        provider_count_evaluated: int,
        providers_evaluated_json: dict,
        providers_not_evaluated_json: dict,
        cache_history: list
    ) -> dict:

        return TradeFlowBuilder.add_step(
            trade=trade,
            name="signal_evaluated",
            payload={
                "signal": {
                    "action": action,
                    "percentage": percentage,
                    "provider_count_configured": provider_count_configured,
                    "provider_count_evaluated": provider_count_evaluated,
                    "providers_evaluated_json": providers_evaluated_json,
                    "providers_not_evaluated_json": providers_not_evaluated_json
                },
                "cache_history": cache_history
            }
        )

    @staticmethod
    def add_risk_assessed(
        trade: dict,
        assessment: dict
    ) -> dict:

        return TradeFlowBuilder.add_step(
            trade=trade,
            name="risk_assessed",
            payload={
                "assessment": assessment
            }
        )

    @staticmethod
    def add_trade_open(
        trade: dict,
        order: dict,
        open_positions: list
    ) -> dict:

        return TradeFlowBuilder.add_step(
            trade=trade,
            name="trade_open",
            payload={
                "order": order,
                "open_positions": open_positions
            }
        )

    @staticmethod
    def add_position_open(
        trade: dict,
        position: dict
    ) -> dict:

        return TradeFlowBuilder.add_step(
            trade=trade,
            name="position_open",
            payload={
                "position": position
            }
        )

    @staticmethod
    def add_trade_close(
        trade: dict,
        order: dict,
        open_positions: list
    ) -> dict:

        return TradeFlowBuilder.add_step(
            trade=trade,
            name="trade_close",
            payload={
                "order": order,
                "open_positions": open_positions
            }
        )

    @staticmethod
    def add_position_close(
        trade: dict,
        position: dict
    ) -> dict:

        return TradeFlowBuilder.add_step(
            trade=trade,
            name="position_close",
            payload={
                "position": position
            }
        )

    @staticmethod
    def add_trade_result(
        trade: dict,
        result: dict,
        open_positions: list
    ) -> dict:

        return TradeFlowBuilder.add_step(
            trade=trade,
            name="trade_result",
            payload={
                "trade": result,
                "open_positions": open_positions
            }
        )

def main():
    market_data = {
        "ticker": "NVDA",
        "t": "2026-08-25T10:15:00Z",
        "open": 181.10,
        "high": 181.35,
        "low": 180.95,
        "close": 181.25,
        "volume": 1250000,
        "vwap": 181.18
    }

    trade = TradeFlowBuilder.initialize(
        market_data=market_data,
        market="Stocks",
        trading_mode="Live"
    )

    print("BEGIN")
    print(json.dumps(trade, indent=4))

    trade = TradeFlowBuilder.add_context(
        trade=trade,
        run_id="Paper_20260825",
        trading_horizon="Swing",
        market_regime="BULLISH_VOLATILE",
        profile_identity="1",
        profile_name="asyafoek-stocks-long-swing-paper",
        side="Long"
    )

    trade = TradeFlowBuilder.add_opportunity_detected(
        trade=trade,
        opportunity_detected=True,
        added_in_cache="20260826T07:32:42+02:00"
    )

    trade = TradeFlowBuilder.add_signal_evaluated(
        trade=trade,
        action="Buy",
        percentage=75,
        provider_count_configured=12,
        provider_count_evaluated=8,
        providers_evaluated_json={},
        providers_not_evaluated_json={},
        cache_history=[]
    )

    trade = TradeFlowBuilder.add_risk_assessed(
        trade=trade,
        assessment={
            "decision": "Accepted",
            "position_sizing": "KellyCriterion",
            "risk_modal": "ATR",
            "risk_reward_ratio": 1.5
        }
    )

    trade = TradeFlowBuilder.add_trade_open(
        trade=trade,
        order={
            "broker": "Alpaca",
            "action": "Buy",
            "requested_size": 6,
            "requested_price": 181.25,
            "status": "Accepted"
        },
        open_positions=[]
    )

    print()
    print("END")
    print(json.dumps(trade, indent=4))    

if __name__ == "__main__":
    main()
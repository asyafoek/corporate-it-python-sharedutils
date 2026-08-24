from datetime import datetime, UTC
from uuid import uuid4


class TradeEvents:

    @staticmethod
    def _base(event_type: str) -> dict:
        return {
            "event_id": f"evt-{uuid4()}",
            "event_type": event_type,
            "event_version": 1,
            "occurred_at": datetime.now(UTC).isoformat()
        }


    @staticmethod
    def watchlist_checked(
        profile: str,
        ticker: str,
        decision: str,
        reason: str,
        **kwargs
    ) -> dict:

        return {
            **TradeEvents._base("WATCHLIST_CHECKED"),

            "profile": profile,
            "ticker": ticker,
            "decision": decision,
            "reason": reason,

            **kwargs
        }
        
    @staticmethod
    def trade_signal(
        profile: str,
        ticker: str,
        signal: str,
        reason: str,
        **kwargs
    ) -> dict:

        return {
            **TradeEvents._base("TRADE_SIGNAL"),

            "profile": profile,
            "ticker": ticker,
            "signal": signal,
            "reason": reason,

            **kwargs
        }


    @staticmethod
    def risk_decision(
        profile: str,
        ticker: str,
        signal: str,
        decision: str,
        reason: str,
        **kwargs
    ) -> dict:

        return {
            **TradeEvents._base("RISK_DECISION"),

            "profile": profile,
            "ticker": ticker,
            "signal": signal,
            "decision": decision,
            "reason": reason,

            **kwargs
        }

    @staticmethod
    def trade_outcome(
        profile: str,
        ticker: str,
        signal: str,
        outcome: str,
        reason: str,
        **kwargs
    ) -> dict:

        return {
            **TradeEvents._base("TRADE_OUTCOME"),

            "profile": profile,
            "ticker": ticker,
            "signal": signal,
            "outcome": outcome,
            "reason": reason,

            **kwargs
        }

if __name__ == "__main__":

    # Watchlist Checked
    event = TradeEvents.watchlist_checked(
        profile="asyafoek-stocks-long",
        ticker="NVDA",
        decision="APPROVED",
        reason="MINIMUM_SIGNAL_STRENGTH_REACHED",
        score=87
    )
    print(event)
    print("\n")

    # Workload Opportunity detected
    event = TradeEvents.trade_signal(
    profile="asyafoek-stocks-long",
    ticker="NVDA",
    signal="BUY",
    reason="PROVIDER_SIGNAL",
    confidence=0.91,
    providers=[
        "RSI",
        "MACD"
    ]
    )

    print(event)
    print("\n")

    # Workload Risk Management Assessed
    event = TradeEvents.risk_decision(
    profile="asyafoek-stocks-long",
    ticker="NVDA",
    signal="BUY",
    decision="APPROVED",
    reason="RISK_CHECK_PASSED"
    )

    print(event)
    print("\n")


    # Trade Execution
    event = TradeEvents.trade_outcome(
        profile="asyafoek-stocks-long",
        ticker="NVDA",
        signal="BUY",
        outcome="FILLED",
        reason="ORDER_EXECUTED",
        trade_id="trade-123",
        order_id="order-456"
    )
    print(event)
    print("\n")

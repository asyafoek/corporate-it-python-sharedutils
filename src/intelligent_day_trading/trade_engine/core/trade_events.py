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


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
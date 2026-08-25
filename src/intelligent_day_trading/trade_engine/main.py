
from intelligent_day_trading.trade_engine.core.trade_events import TradeEvents

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

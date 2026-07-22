import pandas as pd


from intelligent_day_trading.engines.factory import (
    TradingRuleEngineFactory
)


def main():
    print("START")

    profile = {

        "strategy_trading_state":
            "active",

        "strategy_trading_style":
            "momentum",

        "strategy_reward_risk_notation_bullish_quiet":
            "3.0:1",

        "strategy_reward_risk_notation_bullish_volatile":
            "2.0:1",

        "strategy_reward_risk_notation_sideways_quiet":
            "2.0:1",

        "strategy_reward_risk_notation_sideways_volatile":
            "1.5:1",

        "strategy_reward_risk_notation_bearish_quiet":
            "0:0",

        "strategy_reward_risk_notation_bearish_volatile":
            "0:0"
    }

    watchlist_entry = {

        "run_id":
            "RUN_001",

        "market_regime":
            "bullish_quiet",

        "ticker":
            "NVDA",

        "market":
            "stocks"
    }

    market_data = pd.DataFrame(
        [
            {
                "o": 170.0,
                "h": 175.0,
                "l": 169.0,
                "c": 174.0,

                "ema8": 171.0,
                "ema20": 170.0,
                "ema50": 165.0,
                "ema200": 150.0,

                "rsi14": 65.0,

                "volume_ratio": 2.5,

                "high_20": 173.0,
                "high_50": 172.0,
                "high_252": 170.0,

                "low_20": 160.0,

                "atr14": 2.1,

                "relative_strength": 1.4,
                "sector_strength": 1.3,

                "gap_percentage": 4.0,

                "news_sentiment": 0.90
            }
        ],
        index=pd.to_datetime(
            [
                "2026-07-22 15:30:00+00:00"
            ]
        )
    )

    # open_orders = pd.DataFrame()
    open_orders = pd.DataFrame(
        [
            {
                "run_id": "BACKTEST_RUN_001",
                "order_id": "BT_NVDA_001",
                "environment": "BACKTEST",
                "ticker": "NVDA",
                "side": "long",
                "quantity": 100,
                "entry_price": 165.00,
                "current_price": 174.00,
                "unrealized_pnl": 900.00,
                "status": "open"
            },
            {
                "run_id": "LIVE_RUN_001",
                "order_id": "LIVE_NVDA_001",
                "environment": "LIVE",
                "ticker": "NVDA",
                "side": "long",
                "quantity": 50,
                "entry_price": 168.00,
                "current_price": 174.00,
                "unrealized_pnl": 300.00,
                "status": "open"
            },
            {
                "run_id": "LIVE_RUN_002",
                "order_id": "LIVE_MSFT_001",
                "environment": "LIVE",
                "ticker": "MSFT",
                "side": "long",
                "quantity": 20,
                "entry_price": 540.00,
                "current_price": 548.00,
                "unrealized_pnl": 160.00,
                "status": "open"
            }
        ]
    )


    engine = (
        TradingRuleEngineFactory.create(
            version=1
        )
    )

    signals = engine.evaluate(
        profile=profile,
        watchlist_entry=watchlist_entry,
        market_data=market_data,
        open_orders=open_orders
    )

    print()
    print(
        "=" * 80
    )
    print(
        "TRADING SIGNALS"
    )
    print(
        "=" * 80
    )

    if signals.empty:

        print(
            "No signals generated."
        )

        return

    print(
        signals
    )

    print()
    print(
        "=" * 80
    )
    print(
        "FIRST SIGNAL"
    )
    print(
        "=" * 80
    )

    print(
        signals.iloc[0]
        .to_dict()
    )

    print()
    print(
        "=" * 80
    )
    print(
        "JSON"
    )
    print(
        "=" * 80
    )

    print(
        signals.to_json(
            orient="records",
            indent=4
        )
    )


if __name__ == "__main__":
    main()
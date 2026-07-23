import json

import pandas as pd

from intelligent_day_trading.rule_engine.engines.factory import (
    TradingRuleEngineFactory
)


def main():

    print("START")

    profile = {

        "profile_name":
            "asyafoek_stocks_live",

        "profile_identity":
            1,

        "enabled":
            True,

        "account_mode":
            "live",

        "market":
            "stocks",

        "strategy_regime_rule_version":
            1,

        "strategy_trading_horizon":
            "intraday",

        "strategy_trading_side":
            "both",

        "strategy_trading_state":
            "active",

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
            "2.0:1",

        "strategy_position_management_trading_capital":
            5000,

        "strategy_position_management_take_profit_percentage":
            30,

        "strategy_position_management_stop_losing_percentage":
            1,

        "strategy_position_management_max_concurrent_trades":
            3,

        "strategy_position_management_max_trades_per_sector":
            2,

        "strategy_position_management_max_trades_per_ticker":
            3,

        "strategy_position_management_max_trades_per_day":
            100
    }

    watchlist_entry = {

        "run_id":
            "RUN_001",

        "market_regime":
            "bullish_quiet",

        "ticker":
            "NVDA",

        "market":
            "stocks",

        "sector":
            "technology",

        "industry":
            "semiconductors"
    }

    market_data = pd.DataFrame(
        [
            {
                "run_mode": "LIVE",

                "ev": "AM",

                "ticker": "NVDA",

                "o": 170.0,
                "h": 175.0,
                "l": 169.0,
                "c": 174.0,

                "v": 10000,
                "av": 500000,

                "op": 169.0,
                "vw": 173.0,
                "a": 168.0,
                "z": 100,

                "s": 1780000000000,
                "e": 1780000060000,

                "ema8": 171.0,
                "ema20": 170.0,
                "ema50": 165.0,
                "ema200": 150.0,

                "sma20": 169.0,
                "sma50": 164.0,
                "sma200": 148.0,

                "rsi14": 65.0,

                "macd": 1.25,
                "macd_signal": 1.00,
                "macd_histogram": 0.25,

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
            }
        ]
    )

    engine = (
        TradingRuleEngineFactory.create(
            version=1
        )
    )

    result = engine.evaluate(
        profile=profile,
        watchlist_entry=watchlist_entry,
        market_data=market_data,
        open_orders=open_orders
    )

    print()
    print("=" * 80)
    print("TRADING SIGNALS")
    print("=" * 80)

    trading_signals = (
        result.get(
            "trading_signals",
            []
        )
    )

    if not trading_signals:

        print(
            "No signals generated."
        )

        return

    print(
        f"Generated {len(trading_signals)} signal(s)"
    )

    print()
    print("=" * 80)
    print("FIRST SIGNAL")
    print("=" * 80)

    print(
        json.dumps(
            trading_signals[0],
            indent=4,
            default=str
        )
    )

    print()
    print("=" * 80)
    print("JSON")
    print("=" * 80)

    print(
        json.dumps(
            result,
            indent=4,
            default=str
        )
    )


if __name__ == "__main__":
    main()
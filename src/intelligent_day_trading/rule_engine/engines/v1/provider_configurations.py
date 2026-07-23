import pandas as pd


PROVIDERS = [
    "momentum",
    "breakout",
    "trend_following",
    "mean_reversion",
    "reversal",
    "scalping",
    "volatility",
    "news",
    "gap",
    "range",
    "sector_rotation",
    "relative_strength"
]


MARKET_REGIMES = [
    "bullish_quiet",
    "bullish_volatile",
    "sideways_quiet",
    "sideways_volatile",
    "bearish_quiet",
    "bearish_volatile"
]


PROVIDER_CONFIGURATIONS = pd.DataFrame([

    {
        "engine_version": 1,
        "trading_horizon": "intraday",
        "market_regime": market_regime,
        "provider": provider,
        "weight": 1.0
    }

    for market_regime in MARKET_REGIMES

    for provider in PROVIDERS
])
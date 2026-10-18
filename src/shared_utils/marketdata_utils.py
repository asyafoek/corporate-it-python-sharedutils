import re

import pandas as pd
import numpy as np
import json

from math import floor

from decimal import Decimal
from sqlalchemy import text
from zoneinfo import ZoneInfo

from datetime import (
    datetime,
    UTC,
    timedelta
)

from shared_utils.postgres_utils import (
    get_default_engine,
    select_to_json,
    get_schema_dict,
    ensure_schema_and_table,
    store_dicts_into_table,
)

from datetime import (
    datetime,
    timezone
)



# LOOKBACK_DAYS = 7

# BARS_PER_HOUR = 4
# HOURS_PER_DAY = 24

# ROWS_PER_TICKER = (
#     LOOKBACK_DAYS
#     * HOURS_PER_DAY
#     * BARS_PER_HOUR
# )

ROWS_PER_TICKER = 672

INDICATOR_WARMUP_BARS = 400

ATR_PERIOD = 96
ATR10_PERIOD = 10
ATR14_PERIOD = 14

ATR_PERCENTILE_PERIOD = 200
EMA_SLOPE_PERIOD = 10




COLUMNS_TO_KEEP = [
    "ticker",
    "t",

    "vw",

    "atr",
    "atr_10",
    "atr_14",
    "atr_ratio",
    "atr_avg",

    "ema20",
    "ema50",
    "ema200",

    "ema5",
    "ema35",
    "ema50_slope",

    "range_position_20",

    "trend_acceleration",

    "atr_change",

    "rvol_change",

    "distance_to_ema20",
    "distance_to_ema20_atr",

    "distance_to_ema50",
    "distance_to_ema200",

    "ema_alignment_bull",
    "ema_alignment_bear",

    "breakout_readiness",
    "mean_reversion_readiness",

    "volume_avg20",

    "poc_price",
    "vah_price",
    "val_price",

    "distance_to_poc",
    "distance_to_vah",
    "distance_to_val",

    "value_area_position",

    "rvol",

    "keltner_middle",
    "keltner_upper",
    "keltner_lower",

    "anchored_vwap",

    "anchored_vwap_upper_1",
    "anchored_vwap_upper_2",

    "anchored_vwap_lower_1",
    "anchored_vwap_lower_2",

    "distance_to_vwap",
    "vwap_zscore",

    "macd",
    "macd_signal",
    "macd_histogram",

    "adx",

    "trend_strength",

    "plus_di",
    "minus_di",

    "trend_regime",
    "volatility_regime",
    "ticker_regime",

    "resistance_upper",
    "resistance_lower",

    "support_upper",
    "support_lower",

    "rsi_14",

    "rsi_overbought",
    "rsi_oversold",

    "low_20",
    "low_50",
    "low_252",

    "high_20",
    "high_50",
    "high_252",

    "distance_to_high_20",
    "distance_to_high_50",

    "distance_to_low_20",
    "distance_to_low_50",

    "gap_percentage",

    "relative_strength",
    "sector_strength",
    "news_sentiment",
]





# WATCH_SETUP_COLUMNS = [
#     "ticker",
#     "t",
#     "watch_setup",
#     "score"
# ]


WATCH_SETUP_COLUMNS = [
    "ticker",
    "t",
    "watch_setups"
]

# HORIZON_COLUMNS = [
#     "ticker",
#     "t",
#     "horizon",
#     "score"
# ]

HORIZON_COLUMNS = [
    "ticker",
    "t",
    "horizons"
]


VOLUME_PROFILE_LOOKBACK = 200
VOLUME_PROFILE_BINS = 100

def calculate_volume_profile(
    window_df,
    bins=VOLUME_PROFILE_BINS
):

    price_min = window_df["l"].min()
    price_max = window_df["h"].max()

    if price_min == price_max:
        return (
            np.nan,
            np.nan,
            np.nan
        )

    bucket_edges = np.linspace(
        price_min,
        price_max,
        bins + 1
    )

    bucket_centers = (
        bucket_edges[:-1]
        + bucket_edges[1:]
    ) / 2

    volume_per_bucket = np.zeros(
        bins
    )

    for _, row in window_df.iterrows():

        bucket = np.searchsorted(
            bucket_edges,
            row["vw"],
            side="right"
        ) - 1

        bucket = max(
            0,
            min(
                bucket,
                bins - 1
            )
        )

        volume_per_bucket[
            bucket
        ] += row["v"]

    poc_idx = np.argmax(
        volume_per_bucket
    )

    poc_price = bucket_centers[
        poc_idx
    ]

    total_volume = (
        volume_per_bucket.sum()
    )

    target_volume = (
        total_volume * 0.70
    )

    cumulative_volume = (
        volume_per_bucket[poc_idx]
    )

    low_idx = poc_idx
    high_idx = poc_idx

    while (
        cumulative_volume
        < target_volume
    ):

        volume_above = (
            volume_per_bucket[
                high_idx + 1
            ]
            if high_idx < bins - 1
            else -1
        )

        volume_below = (
            volume_per_bucket[
                low_idx - 1
            ]
            if low_idx > 0
            else -1
        )

        if volume_above >= volume_below:

            high_idx += 1
            cumulative_volume += (
                volume_above
            )

        else:

            low_idx -= 1
            cumulative_volume += (
                volume_below
            )

    val_price = bucket_centers[
        low_idx
    ]

    vah_price = bucket_centers[
        high_idx
    ]

    return (
        poc_price,
        vah_price,
        val_price
    )

def add_volume_profile_indicators(
    group,
    lookback=VOLUME_PROFILE_LOOKBACK
):

    group["poc_price"] = np.nan
    group["vah_price"] = np.nan
    group["val_price"] = np.nan

    for i in range(len(group)):

        window = group.iloc[
            max(0, i - lookback + 1):i + 1
        ]

        poc, vah, val = (
            calculate_volume_profile(
                window
            )
        )

        idx = group.index[i]

        group.at[idx, "poc_price"] = poc
        group.at[idx, "vah_price"] = vah
        group.at[idx, "val_price"] = val

    group["distance_to_poc"] = (
        (group["vw"] - group["poc_price"])
        /
        group["poc_price"]
    )

    group["distance_to_vah"] = (
        (group["vw"] - group["vah_price"])
        /
        group["vah_price"]
    )

    group["distance_to_val"] = (
        (group["vw"] - group["val_price"])
        /
        group["val_price"]
    )

    group["value_area_position"] = (
        (
            group["vw"]
            - group["val_price"]
        )
        /
        (
            group["vah_price"]
            - group["val_price"]
        ).replace(
            0,
            np.nan
        )
    )

    return group


def calculate_adx(
    df,
    period=14
):

    # df = df.copy()

    # True Range
    high_low = (
        df["h"]
        -
        df["l"]
    )

    high_close = np.abs(
        df["h"]
        -
        df["c"].shift(1)
    )

    low_close = np.abs(
        df["l"]
        -
        df["c"].shift(1)
    )

    # tr = pd.concat(
    #     [
    #         high_low,
    #         high_close,
    #         low_close
    #     ],
    #     axis=1
    # ).max(
    #     axis=1
    # )

    tr = np.maximum.reduce([
        high_low.values,
        high_close.values,
        low_close.values
    ])

    tr = pd.Series(
        tr,
        index=df.index
    )

    # Directional movement

    up_move = (
        df["h"]
        -
        df["h"].shift(1)
    )

    down_move = (
        df["l"].shift(1)
        -
        df["l"]
    )


    plus_dm = np.where(
        (up_move > down_move)
        &
        (up_move > 0),
        up_move,
        0
    )

    minus_dm = np.where(
        (down_move > up_move)
        &
        (down_move > 0),
        down_move,
        0
    )


    # Wilder smoothing

    atr = (
        tr
        .ewm(
            alpha=1/period,
            adjust=False
        )
        .mean()
    )

    plus_di = (
        pd.Series(
            plus_dm,
            index=df.index
        )
        .ewm(
            alpha=1/period,
            adjust=False
        )
        .mean()
        /
        atr
        *
        100
    )


    minus_di = (
        pd.Series(
            minus_dm,
            index=df.index
        )
        .ewm(
            alpha=1/period,
            adjust=False
        )
        .mean()
        /
        atr
        *
        100
    )


    dx = (
        np.abs(
            plus_di
            -
            minus_di
        )
        /
        (
            plus_di
            +
            minus_di
        ).replace(
            0,
            np.nan
        )
    ) * 100


    adx = (
        dx
        .ewm(
            alpha=1/period,
            adjust=False
        )
        .mean()
    )


    df["plus_di"] = plus_di
    df["minus_di"] = minus_di
    df["adx"] = adx

    return df


def calculate_indicators(
    df
):

    df = df.sort_values(
        ["ticker", "t"]
    ).copy()

    # result = []
    records = []

    df["trade_date"] = (
        pd.to_datetime(
            df["t"],
            unit="ms",
            utc=True
        )
        .dt.date
    )

    for ticker, group in df.groupby(
        "ticker"
    ):

        # print(
        #     f"Processing ticker: {ticker}"
        # )

        # group = group.copy()

        # group["trade_date"] = (
        #     pd.to_datetime(
        #         group["t"],
        #         unit="ms",
        #         utc=True
        #     )
        #     .dt.date
        # )

        # GAP %

        daily_stats = (
            group
            .groupby("trade_date")
            .agg(
                day_open=("c", "first"),
                day_close=("c", "last")
            )
        )

        daily_stats["prev_day_close"] = (
            daily_stats["day_close"]
            .shift(1)
        )

        # group = (
        #     group
        #     .merge(
        #         daily_stats[
        #             [
        #                 "day_open",
        #                 "prev_day_close"
        #             ]
        #         ],
        #         left_on="trade_date",
        #         right_index=True,
        #         how="left"
        #     )
        # )

        group["day_open"] = (
            group["trade_date"]
            .map(daily_stats["day_open"])
        )

        group["prev_day_close"] = (
            group["trade_date"]
            .map(
                daily_stats["prev_day_close"]
            )
        )

        group["gap_percentage"] = (
            (
                group["day_open"]
                -
                group["prev_day_close"]
            )
            /
            group["prev_day_close"]
            .replace(
                0,
                np.nan
            )
        ) * 100

        latest_day = (
            group["trade_date"]
            .max()
        )

        # high_low = (
        #     group["h"]
        #     - group["l"]
        # )

        # high_cp = np.abs(
        #     group["h"]
        #     - group["c"].shift()
        # )

        # low_cp = np.abs(
        #     group["l"]
        #     - group["c"].shift()
        # )

        # tr = pd.concat(
        #     [
        #         high_low,
        #         high_cp,
        #         low_cp
        #     ],
        #     axis=1
        # ).max(
        #     axis=1
        # )

        prev_close = group["c"].shift()

        tr = np.maximum.reduce([
            (group["h"] - group["l"]).values,
            np.abs(group["h"] - prev_close).values,
            np.abs(group["l"] - prev_close).values
        ])

        tr = pd.Series(
            tr,
            index=group.index
        )

        # ==================================================
        # ATR OVER FULL HISTORY
        # ==================================================


        group["atr_10"] = (
            tr
            .rolling(
                window=10,
                min_periods=1
            )
            .mean()
        )

        group["atr_14"] = (
            tr
            .rolling(
                window=14,
                min_periods=1
            )
            .mean()
        )

        # group["atr"] = (
        #     tr
        #     .rolling(
        #         window=ATR_PERIOD,
        #         min_periods=1
        #     )
        #     .mean()
        #     .bfill()
        # )

        group["atr"] = (
            tr
            .ewm(
                alpha=1/ATR_PERIOD,
                adjust=False
            )
            .mean()
        )

        group["ema20"] = (
            group["c"]
            .ewm(
                span=20,
                adjust=False
            )
            .mean()
        )

        group["ema50"] = (
            group["c"]
            .ewm(
                span=50,
                adjust=False
            )
            .mean()
        )

        group["ema200"] = (
            group["c"]
            .ewm(
                span=200,
                adjust=False
            )
            .mean()
        )

        group["ema5"] = (
            group["c"]
            .ewm(
                span=5,
                adjust=False
            )
            .mean()
        )

        group["ema35"] = (
            group["c"]
            .ewm(
                span=35,
                adjust=False
            )
            .mean()
        )

        group["ema50_slope"] = (
            group["ema50"]
            .pct_change(EMA_SLOPE_PERIOD)
        )

        group["trend_acceleration"] = (
            group["ema50_slope"]
            -
            group["ema50_slope"].shift(5)
        )

        group["ema_alignment_bull"] = (
            (
                group["ema20"]
                > group["ema50"]
            )
            &
            (
                group["ema50"]
                > group["ema200"]
            )
        )

        group["ema_alignment_bear"] = (
            (
                group["ema20"]
                < group["ema50"]
            )
            &
            (
                group["ema50"]
                < group["ema200"]
            )
        )



        group["distance_to_ema20"] = (
            (
                group["vw"]
                - group["ema20"]
            )
            /
            group["ema20"]
        )

        group["distance_to_ema50"] = (
            (
                group["vw"]
                - group["ema50"]
            )
            /
            group["ema50"]
        )

        group["distance_to_ema200"] = (
            (
                group["vw"]
                - group["ema200"]
            )
            /
            group["ema200"]
        )        
        
        group["distance_to_ema20_atr"] = (
            (
                group["vw"]
                -
                group["ema20"]
            )
            /
            group["atr"]
        )

        group["keltner_middle"] = group["ema20"]

        group["keltner_upper"] = (
            group["ema20"]
            +
            (
                group["atr_10"]
                * 1.5
            )
        )

        group["keltner_lower"] = (
            group["ema20"]
            -
            (
                group["atr_10"]
                * 1.5
            )
        )


        # ==========================================
        # ANCHORED VWAP
        # ==========================================

        group["typical_price"] = (
            group["h"]
            + group["l"]
            + group["c"]
        ) / 3.0

        group["cum_tpv"] = (
            group["typical_price"]
            * group["v"]
        ).groupby(
            group["trade_date"]
        ).cumsum()

        group["cum_vol"] = (
            group["v"]
        ).groupby(
            group["trade_date"]
        ).cumsum()

        group["anchored_vwap"] = (
            group["cum_tpv"]
            /
            group["cum_vol"]
            .replace(0, np.nan)
        )

        group["distance_to_vwap"] = (
            (
                group["vw"]
                - group["anchored_vwap"]
            )
            /
            group["anchored_vwap"]
        )

        # ==========================================
        # AVWAP STANDARD DEVIATION BANDS
        # ==========================================

        group["avwap_std"] = (
            group
            .groupby("trade_date")["c"]
            .expanding()
            .std(ddof=0)
            .reset_index(level=0, drop=True)
        )

        group["vwap_zscore"] = (
            (
                group["vw"]
                - group["anchored_vwap"]
            )
            /
            group["avwap_std"].replace(
                0,
                np.nan
            )
        )

        group["anchored_vwap_upper_1"] = (
            group["anchored_vwap"]
            +
            group["avwap_std"]
        )

        group["anchored_vwap_upper_2"] = (
            group["anchored_vwap"]
            +
            (
                group["avwap_std"]
                * 2
            )
        )

        group["anchored_vwap_lower_1"] = (
            group["anchored_vwap"]
            -
            group["avwap_std"]
        )

        group["anchored_vwap_lower_2"] = (
            group["anchored_vwap"]
            -
            (
                group["avwap_std"]
                * 2
            )
        )

        group["macd"] = (
            group["ema5"]
            -
            group["ema35"]
        )

        group["macd_signal"] = (
            group["macd"]
            .ewm(
                span=5,
                adjust=False
            )
            .mean()
        )

        group["macd_histogram"] = (
            group["macd"]
            -
            group["macd_signal"]
        )

        # RSI

        delta = group["c"].diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        # avg_gain = gain.rolling(
        #     14,
        #     min_periods=14
        # ).mean()

        # avg_loss = loss.rolling(
        #     14,
        #     min_periods=14
        # ).mean()

        avg_gain = gain.ewm(
            alpha=1/14,
            adjust=False,
            min_periods=14
        ).mean()

        avg_loss = loss.ewm(
            alpha=1/14,
            adjust=False,
            min_periods=14
        ).mean()

        rs = (
            avg_gain
            /
            avg_loss.replace(
                0,
                np.nan
            )
        )

        group["rsi_14"] = (
            100
            -
            (
                100
                /
                (
                    1
                    +
                    rs
                )
            )
        )

        group["rsi_overbought"] = (
            group["rsi_14"] >= 70
        )

        group["rsi_oversold"] = (
            group["rsi_14"] <= 30
        )

        # Breakouts low
        group["low_20"] = (
            group["l"]
            .rolling(
                20,
                min_periods=1
            )
            .min()
        )

        group["low_50"] = (
            group["l"]
            .rolling(
                50,
                min_periods=1
            )
            .min()
        )

        group["low_252"] = (
            group["l"]
            .rolling(
                252,
                min_periods=1
            )
            .min()
        )



        # Breakout highs

        group["high_20"] = (
            group["h"]
            .rolling(
                20,
                min_periods=1
            )
            .max()
        )

        group["high_50"] = (
            group["h"]
            .rolling(
                50,
                min_periods=1
            )
            .max()
        )

        group["high_252"] = (
            group["h"]
            .rolling(
                252,
                min_periods=1
            )
            .max()
        )

        group["range_position_20"] = (
            (
                group["vw"]
                - group["low_20"]
            )
            /
            (
                group["high_20"]
                - group["low_20"]
            ).replace(
                0,
                np.nan
            )
        )

        group["distance_to_high_20"] = (
            (
                group["high_20"]
                - group["vw"]
            )
            /
            group["high_20"]
        )

        group["distance_to_high_50"] = (
            (
                group["high_50"]
                - group["vw"]
            )
            /
            group["high_50"]
        )

        group["distance_to_low_20"] = (
            (
                group["vw"]
                - group["low_20"]
            )
            /
            group["low_20"]
        )

        group["distance_to_low_50"] = (
            (
                group["vw"]
                - group["low_50"]
            )
            /
            group["low_50"]
        )

        group["breakout_readiness"] = (
            (1 - group["distance_to_high_20"])
            .clip(0, 1)
        )

        group["mean_reversion_readiness"] = (
            np.abs(
                group["vwap_zscore"]
            )
        )

        group["volume_avg20"] = (
            group["v"]
            .rolling(
                window=20,
                min_periods=20
            )
            .mean()
        )

        group["rvol"] = (
            group["v"]
            /
            group["volume_avg20"]
        )        

        group["rvol_change"] = (
            group["rvol"]
            .pct_change(5)
        )


        # group["poc_price"] = np.nan
        # group["vah_price"] = np.nan
        # group["val_price"] = np.nan

        # group["distance_to_poc"] = np.nan
        # group["distance_to_vah"] = np.nan
        # group["distance_to_val"] = np.nan

        # group["value_area_position"] = np.nan


        group = add_volume_profile_indicators(
            group
        )

        group = calculate_adx(group)

        group["trend_strength"] = (
            group["adx"] / 100.0
        )

        # group["atr_avg"] = (
        #     group["atr"]
        #     .rolling(
        #         window=252,
        #         min_periods=1
        #     )
        #     .mean()
        # )

        group["atr_avg"] = (
            group["atr"]
            .rolling(
                window=252,
                min_periods=50
            )
            .median()
        )

        group["atr_ratio"] = (
            group["atr"]
            /
            group["atr_avg"]
        )

        group["atr_change"] = (
            group["atr_ratio"]
            .pct_change(10)
        )

        # ==================================================
        # ONLY KEEP MOST RECENT DAY
        # ==================================================

        # Placeholder enrichment fields

        group["relative_strength"] = None
        group["sector_strength"] = None
        group["news_sentiment"] = None

        # today_group = group[
        #     group["trade_date"]
        #     == latest_day
        # ].copy()

        today_group = group[
            group["trade_date"]
            == latest_day
        ]

        # today_group["trend_regime"] = np.where(
        #     (
        #         today_group["c"]
        #         >
        #         today_group["ema200"]
        #     )
        #     &
        #     (
        #         today_group["ema20"]
        #         >
        #         today_group["ema50"]
        #     ),
        #     "BULLISH",
        #     np.where(
        #         (
        #             today_group["c"]
        #             <
        #             today_group["ema200"]
        #         )
        #         &
        #         (
        #             today_group["ema20"]
        #             <
        #             today_group["ema50"]
        #         ),
        #         "BEARISH",
        #         "SIDEWAYS"
        #     )
        # )


        # today_group["trend_regime"] = np.where(
        #     (
        #         (today_group["c"] > today_group["ema50"])
        #         &
        #         (today_group["ema50"] > today_group["ema200"])
        #         &
        #         (today_group["adx"] >= 25)
        #         &
        #         (today_group["plus_di"] > today_group["minus_di"])
        #     ),
        #     "BULLISH",
        #     np.where(
        #         (
        #             (today_group["c"] < today_group["ema50"])
        #             &
        #             (today_group["ema50"] < today_group["ema200"])
        #             &
        #             (today_group["adx"] >= 25)
        #             &
        #             (today_group["minus_di"] > today_group["plus_di"])
        #         ),
        #         "BEARISH",
        #         "SIDEWAYS"
        #     )
        # )


        today_group["trend_regime"] = np.select(
            [
                (
                    (today_group["ema20"] > today_group["ema50"]) &
                    (today_group["ema50"] > today_group["ema200"]) &
                    (today_group["ema50_slope"] > 0)
                ),

                (
                    (today_group["ema20"] < today_group["ema50"]) &
                    (today_group["ema50"] < today_group["ema200"]) &
                    (today_group["ema50_slope"] < 0)
                )
            ],
            [
                "BULL",
                "BEAR"
            ],
            default="SIDEWAYS"
        )

        today_group["volatility_regime"] = np.where(
            # today_group["atr_ratio"] >= 1.25,
            today_group["atr_ratio"] >= 1.00,
            "VOLATILE",
            "QUIET"
        )

        today_group["ticker_regime"] = (
            today_group["trend_regime"]
            +
            "_"
            +
            today_group["volatility_regime"]
        )


        if today_group.empty:

            continue

        # ==================================================
        # SUPPORT / RESISTANCE ONLY FOR LATEST DAY
        # ==================================================

        today_group[
            "rolling_max"
        ] = (
            today_group["h"]
            .cummax()
        )

        today_group[
            "rolling_min"
        ] = (
            today_group["l"]
            .cummin()
        )

        today_group[
            "resistance_upper"
        ] = (
            today_group["rolling_max"]
            + (
                today_group["atr"]
                * 0.25
            )
        )

        today_group[
            "resistance_lower"
        ] = (
            today_group["rolling_max"]
            - (
                today_group["atr"]
                * 0.25
            )
        )

        today_group[
            "support_upper"
        ] = (
            today_group["rolling_min"]
            + (
                today_group["atr"]
                * 0.25
            )
        )

        today_group[
            "support_lower"
        ] = (
            today_group["rolling_min"]
            - (
                today_group["atr"]
                * 0.25
            )
        )

        # today_group[
        #     "ticker"
        # ] = ticker

        # result.append(
        #     today_group
        # )

        records.extend(
            today_group.to_dict(
                orient="records"
            )
        )

    # if not result:

    #     return pd.DataFrame()

    # return pd.concat(
    #     result,
    #     ignore_index=True
    # )

    if not records:

        return pd.DataFrame()

    return pd.DataFrame(
        records
    )


def run_indicator_pipeline(
    source_table,
    target_table
):

    print(
        "Using github python shared utils"
    )

    (
        user,
        password,
        db,
        schema,
        host,
        port,
        engine
    ) = get_default_engine()

    sql = f"""
        WITH ranked AS (
            SELECT
                ticker,
                t,
                h,
                l,
                c,
                v,
                vw,
                ROW_NUMBER() OVER (
                    PARTITION BY ticker
                    ORDER BY t DESC
                ) AS rn
            FROM raw.{source_table}
        )
        SELECT
            ticker,
            t,
            h,
            l,
            c,
            v,
            vw
        FROM ranked
        WHERE rn <= {ROWS_PER_TICKER}
        ORDER BY
            ticker,
            t
    """

    rows = select_to_json(
        engine,
        sql,
        params={}
    )

    if not rows:

        print(
            "No source data found"
        )

        return

    print(
        f"Rows loaded: "
        f"{len(rows)}"
    )

    df = pd.DataFrame(
        rows
    )

    sizes = (
        df.groupby("ticker")
        .size()
    )

    print(
        sizes.describe()
    )

    df = (
        df
        .sort_values(
            ["ticker", "t"]
        )
        .groupby(
            "ticker",
            group_keys=False
        )
        .tail(
            INDICATOR_WARMUP_BARS
        )
        .reset_index(
            drop=True
        )
    )

    for col in [
        "h",
        "l",
        "c",
        "v",
        "vw"
    ]:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    print("INPUT")
    print(
        df.columns.tolist()
    )

    result_df = (
        calculate_indicators(
            df
        )
    )

    if result_df.empty:

        print(
            "No indicator rows generated"
        )

        return

    print("OUTPUT")
    print(
        result_df.columns.tolist()
    )

    min_t = int(
        result_df["t"].min()
    )

    max_t = int(
        result_df["t"].max()
    )

    existing_sql = f"""
        SELECT
            ticker,
            t
        FROM raw.{target_table}
        WHERE t BETWEEN {min_t}
        AND {max_t}
    """

    try:

        existing_rows = (
            select_to_json(
                engine,
                existing_sql,
                params={}
            )
        )

    except Exception:

        print(
            f"{target_table} "
            f"does not exist yet"
        )

        existing_rows = []

    if existing_rows:

        existing_df = (
            pd.DataFrame(
                existing_rows
            )
        )

        before_count = len(
            result_df
        )

        result_df = (
            result_df
            .merge(
                existing_df[
                    [
                        "ticker",
                        "t"
                    ]
                ],
                on=[
                    "ticker",
                    "t"
                ],
                how="left",
                indicator=True
            )
        )

        result_df = (
            result_df[
                result_df["_merge"]
                == "left_only"
            ]
            .drop(
                columns="_merge"
            )
        )

        print(
            f"Removed "
            f"{before_count - len(result_df)} "
            f"existing rows"
        )

    if result_df.empty:

        print(
            "No new rows remaining"
        )

        return

    result_df = (
        result_df[
            COLUMNS_TO_KEEP
        ]
        .replace(
            {
                np.nan: None
            }
        )
    )

    records = (
        result_df
        .to_dict(
            orient="records"
        )
    )

    if not records:

        print(
            "No records generated"
        )

        return

    schema_dict = (
        get_schema_dict(
            records
        )
    )

    if "relative_strength" in schema_dict:

        schema_dict[
            "relative_strength"
        ] = Decimal("0")

    if "sector_strength" in schema_dict:

        schema_dict[
            "sector_strength"
        ] = Decimal("0")

    if "news_sentiment" in schema_dict:

        schema_dict[
            "news_sentiment"
        ] = Decimal("0")

    ensure_schema_and_table(
        engine,
        "raw",
        target_table,
        schema_dict,
        None,
        False,
        False
    )

    print(
        f"Upserting "
        f"{len(records)} "
        f"records into "
        f"{target_table}"
    )

    store_dicts_into_table(
        engine,
        records,
        "raw",
        target_table,
        upsert=True,
        ignore_keys=set(),
        use_bulk=True,
        conflict_cols=[
            "ticker",
            "t"
        ]
    )

    print(
        "Finished"
    )


def clamp(
    value,
    minimum=0.0,
    maximum=100.0
):

    return max(
        minimum,
        min(
            maximum,
            value
        )
    )



def calculate_horizon_scores(
    df
):

    work = df.copy()

    work["atr_ratio"] = pd.to_numeric(
        work["atr_ratio"],
        errors="coerce"
    ).fillna(0)

    work["rvol"] = pd.to_numeric(
        work["rvol"],
        errors="coerce"
    ).fillna(0)

    work["trend_strength"] = pd.to_numeric(
        work["trend_strength"],
        errors="coerce"
    ).fillna(0)

    work["trend_strength_pct"] = (
        work["trend_strength"] * 100.0
    )

    work["trend_regime"] = (
        work["trend_regime"]
        .fillna("")
        .astype(str)
        .str.upper()
    )

    work["volatility_regime"] = (
        work["volatility_regime"]
        .fillna("")
        .astype(str)
        .str.upper()
    )

    #
    # SCALPING
    #

    work["scalping_score"] = np.where(
        work["atr_ratio"] > 0,
        np.minimum(
            40,
            work["atr_ratio"] * 400
        ),
        0
    )

    work["scalping_score"] += np.where(
        work["rvol"] > 1,
        np.minimum(
            30,
            (
                work["rvol"] - 1
            ) * 30
        ),
        0
    )

    work["scalping_score"] += np.where(
        work["volatility_regime"].isin(
            [
                "VOLATILE",
                "HIGH"
            ]
        ),
        20,
        0
    )

    work["scalping_score"] += np.where(
        work["trend_regime"].isin(
            [
                "BULL",
                "BEAR"
            ]
        ),
        10,
        0
    )

    work["scalping_score"] = (
        work["scalping_score"]
        .clip(0, 100)
        .round(2)
    )

    #
    # INTRADAY
    #

    work["intraday_score"] = np.where(
        work["atr_ratio"] > 0,
        np.minimum(
            30,
            work["atr_ratio"] * 300
        ),
        0
    )

    work["intraday_score"] += np.where(
        work["rvol"] > 1,
        np.minimum(
            25,
            (
                work["rvol"] - 1
            ) * 25
        ),
        0
    )

    work["intraday_score"] += np.minimum(
        35,
        work["trend_strength_pct"] * 0.35
    )

    work["intraday_score"] += np.where(
        work["trend_regime"].isin(
            [
                "BULL",
                "BEAR"
            ]
        ),
        10,
        0
    )

    work["intraday_score"] = (
        work["intraday_score"]
        .clip(0, 100)
        .round(2)
    )

    #
    # SWING
    #

    work["swing_score"] = np.minimum(
        50,
        work["trend_strength_pct"] * 0.50
    )

    work["swing_score"] += np.where(
        work["trend_regime"].isin(
            [
                "BULL",
                "BEAR"
            ]
        ),
        25,
        0
    )

    work["swing_score"] -= np.where(
        work["volatility_regime"].isin(
            [
                "VOLATILE",
                "HIGH"
            ]
        ),
        5,
        0
    )

    work["swing_score"] -= np.where(
        work["trend_regime"] == "SIDEWAYS",
        15,
        0
    )

    work["swing_score"] = (
        work["swing_score"]
        .clip(0, 100)
        .round(2)
    )

    #
    # POSITION
    #

    work["position_score"] = np.minimum(
        55,
        work["trend_strength_pct"] * 0.55
    )

    work["position_score"] += np.where(
        work["trend_regime"].isin(
            [
                "BULL",
                "BEAR"
            ]
        ),
        30,
        0
    )

    work["position_score"] -= np.where(
        work["volatility_regime"].isin(
            [
                "VOLATILE",
                "HIGH"
            ]
        ),
        10,
        0
    )

    work["position_score"] -= np.where(
        work["trend_regime"] == "SIDEWAYS",
        20,
        0
    )

    work["position_score"] = (
        work["position_score"]
        .clip(0, 100)
        .round(2)
    )

    #
    # INVESTMENT
    #

    work["investment_score"] = np.minimum(
        60,
        work["trend_strength_pct"] * 0.60
    )

    work["investment_score"] += np.where(
        work["trend_regime"].isin(
            [
                "BULL",
                "BEAR"
            ]
        ),
        25,
        0
    )

    work["investment_score"] -= np.where(
        work["volatility_regime"].isin(
            [
                "VOLATILE",
                "HIGH"
            ]
        ),
        15,
        0
    )

    work["investment_score"] -= np.where(
        work["trend_regime"] == "SIDEWAYS",
        20,
        0
    )

    work["investment_score"] = (
        work["investment_score"]
        .clip(0, 100)
        .round(2)
    )

    # frames = []

    # mapping = [
    #     (
    #         "Scalping",
    #         "scalping_score"
    #     ),
    #     (
    #         "Intraday",
    #         "intraday_score"
    #     ),
    #     (
    #         "Swing",
    #         "swing_score"
    #     ),
    #     (
    #         "Position",
    #         "position_score"
    #     ),
    #     (
    #         "Investment",
    #         "investment_score"
    #     )
    # ]

    # for (
    #     horizon,
    #     score_column
    # ) in mapping:

    #     tmp = work[
    #         [
    #             "ticker",
    #             "t"
    #         ]
    #     ].copy()

    #     tmp["horizon"] = horizon

    #     tmp["score"] = (
    #         work[
    #             score_column
    #         ]
    #     )

    #     frames.append(
    #         tmp
    #     )

    # return pd.concat(
    #     frames,
    #     ignore_index=True
    # )

    work["horizons"] = work.apply(
        lambda row: {
            "Scalping": float(
                row["scalping_score"]
            ),
            "Intraday": float(
                row["intraday_score"]
            ),
            "Swing": float(
                row["swing_score"]
            ),
            "Position": float(
                row["position_score"]
            ),
            "Investment": float(
                row["investment_score"]
            )
        },
        axis=1
    )

    return work[
        [
            "ticker",
            "t",
            "horizons"
        ]
    ].copy()

def run_horizon_pipeline(
    source_table,
    target_table
):

    print(
        "Using github python shared utils"
    )

    (
        user,
        password,
        db,
        schema,
        host,
        port,
        engine
    ) = get_default_engine()

    sql = f"""
        SELECT
            ticker,
            t,

            atr_ratio,
            rvol,

            trend_strength,
            trend_regime,
            volatility_regime

        FROM raw.{source_table}

        WHERE t = (
            SELECT MAX(t)
            FROM raw.{source_table}
        )

        ORDER BY ticker
    """

    rows = select_to_json(
        engine,
        sql,
        params={}
    )

    if not rows:

        print(
            "No source data found"
        )

        return

    df = pd.DataFrame(
        rows
    )

    result_df = (
        calculate_horizon_scores(
            df
        )
    )

    if result_df.empty:

        print(
            "No horizon rows generated"
        )

        return

    result_df = (
        result_df[
            HORIZON_COLUMNS
        ]
        .replace(
            {
                np.nan: None
            }
        )
    )

    records = (
        result_df
        .to_dict(
            orient="records"
        )
    )

    if not records:

        print(
            "No records generated"
        )

        return

    schema_dict = (
        get_schema_dict(
            records
        )
    )

    ensure_schema_and_table(
        engine,
        "raw",
        target_table,
        schema_dict,
        None,
        False,
        False
    )

    store_dicts_into_table(
        engine,
        records,
        "raw",
        target_table,
        upsert=True,
        ignore_keys=set(),
        use_bulk=True,
        # conflict_cols=[
        #     "ticker",
        #     "t",
        #     "horizon"
        # ]
        conflict_cols=[
            "ticker",
            "t"
        ]
    )

    print(
        f"Finished - stored "
        f"{len(records)} horizon rows"
    )


def calculate_watch_setups(
    df
):
    work = df.copy()

    work["atr_ratio"] = pd.to_numeric(
        work["atr_ratio"],
        errors="coerce"
    ).fillna(0)

    work["rvol"] = pd.to_numeric(
        work["rvol"],
        errors="coerce"
    ).fillna(0)

    work["trend_strength_pct"] = (
        pd.to_numeric(
            work["trend_strength"],
            errors="coerce"
        ).fillna(0)
        * 100
    )

    work["trend_regime"] = (
        work["trend_regime"]
        .fillna("")
        .str.upper()
    )

    work["rsi_14"] = pd.to_numeric(
        work["rsi_14"],
        errors="coerce"
    ).fillna(50)

    work["macd_histogram"] = pd.to_numeric(
        work["macd_histogram"],
        errors="coerce"
    ).fillna(0)

    #
    # BREAKOUT
    #

    work["breakout_score"] = np.minimum(
        30,
        work["atr_ratio"] * 300
    )

    work["breakout_score"] += np.where(
        work["rvol"] > 1,
        np.minimum(
            30,
            (work["rvol"] - 1) * 30
        ),
        0
    )

    work["breakout_score"] += np.where(
        work["trend_strength_pct"] > 50,
        np.minimum(
            20,
            (work["trend_strength_pct"] - 50) * 0.4
        ),
        0
    )

    work["breakout_score"] += 20

    work["breakout_score"] = (
        work["breakout_score"]
        .clip(0, 100)
        .round(2)
    )

    #
    # MOMENTUM
    #

    work["momentum_score"] = np.where(
        work["trend_strength_pct"] > 40,
        np.minimum(
            35,
            work["trend_strength_pct"] * 0.35
        ),
        0
    )

    work["momentum_score"] += np.where(
        work["rvol"] > 1,
        np.minimum(
            25,
            (work["rvol"] - 1) * 25
        ),
        0
    )

    work["momentum_score"] += np.where(
        work["trend_regime"].isin(
            ["BULL", "BEAR"]
        ),
        20,
        0
    )

    work["momentum_score"] += np.where(
        work["macd_histogram"].abs() > 0,
        20,
        0
    )

    work["momentum_score"] = (
        work["momentum_score"]
        .clip(0, 100)
        .round(2)
    )

    #
    # PULLBACK
    #

    work["pullback_score"] = np.where(
        work["trend_regime"].isin(
            ["BULL", "BEAR"]
        ),
        35,
        0
    )

    work["pullback_score"] += np.where(
        (
            (work["rsi_14"] >= 40)
            &
            (work["rsi_14"] <= 60)
        ),
        20,
        0
    )

    work["pullback_score"] += np.where(
        work["trend_strength_pct"] >= 50,
        25,
        0
    )

    work["pullback_score"] += np.where(
        work["rvol"] < 1,
        20,
        0
    )

    work["pullback_score"] = (
        work["pullback_score"]
        .clip(0, 100)
        .round(2)
    )

    #
    # REVERSAL
    #

    work["reversal_score"] = np.where(
        (
            (work["rsi_14"] <= 30)
            |
            (work["rsi_14"] >= 70)
        ),
        40,
        0
    )

    work["reversal_score"] += np.where(
        work["trend_regime"] == "SIDEWAYS",
        20,
        0
    )

    work["reversal_score"] += np.where(
        work["macd_histogram"].abs() > 0,
        20,
        0
    )

    work["reversal_score"] += np.where(
        work["rvol"] > 1.5,
        20,
        0
    )

    work["reversal_score"] = (
        work["reversal_score"]
        .clip(0, 100)
        .round(2)
    )

    #
    # MEAN REVERSION
    #

    work["mean_reversion_score"] = np.where(
        work["trend_regime"] == "SIDEWAYS",
        40,
        0
    )

    work["mean_reversion_score"] += np.where(
        (
            (work["rsi_14"] >= 30)
            &
            (work["rsi_14"] <= 70)
        ),
        20,
        0
    )

    work["mean_reversion_score"] += np.where(
        work["trend_strength_pct"] < 40,
        20,
        0
    )

    work["mean_reversion_score"] += np.where(
        work["rvol"] < 1,
        20,
        0
    )

    work["mean_reversion_score"] = (
        work["mean_reversion_score"]
        .clip(0, 100)
        .round(2)
    )

    #
    # RANGE
    #

    work["range_score"] = np.where(
        work["trend_regime"] == "SIDEWAYS",
        50,
        0
    )

    work["range_score"] += np.where(
        work["trend_strength_pct"] < 35,
        25,
        0
    )

    work["range_score"] += np.where(
        work["rvol"] < 1,
        25,
        0
    )

    work["range_score"] = (
        work["range_score"]
        .clip(0, 100)
        .round(2)
    )

    #
    # TREND CONTINUATION
    #

    work["trend_continuation_score"] = np.where(
        work["trend_regime"].isin(
            ["BULL", "BEAR"]
        ),
        40,
        0
    )

    work["trend_continuation_score"] += np.minimum(
        40,
        work["trend_strength_pct"] * 0.4
    )

    work["trend_continuation_score"] += np.where(
        (
            (work["ema20"] > work["ema50"])
            &
            (work["trend_regime"] == "BULL")
        ),
        20,
        0
    )

    work["trend_continuation_score"] += np.where(
        (
            (work["ema20"] < work["ema50"])
            &
            (work["trend_regime"] == "BEAR")
        ),
        20,
        0
    )

    work["trend_continuation_score"] = (
        work["trend_continuation_score"]
        .clip(0, 100)
        .round(2)
    )

    # frames = []

    # mapping = [
    #     ("Breakout", "breakout_score"),
    #     ("Momentum", "momentum_score"),
    #     ("Pullback", "pullback_score"),
    #     ("Reversal", "reversal_score"),
    #     ("MeanReversion", "mean_reversion_score"),
    #     ("Range", "range_score"),
    #     ("TrendContinuation", "trend_continuation_score")
    # ]

    # for setup_name, score_col in mapping:

    #     tmp = work[
    #         ["ticker", "t"]
    #     ].copy()

    #     tmp["watch_setup"] = setup_name

    #     tmp["score"] = work[
    #         score_col
    #     ]

    #     frames.append(tmp)

    # return pd.concat(
    #     frames,
    #     ignore_index=True
    # )

    work["watch_setups"] = work.apply(
        lambda row: {
            "Breakout": float(row["breakout_score"]),
            "Momentum": float(row["momentum_score"]),
            "Pullback": float(row["pullback_score"]),
            "Reversal": float(row["reversal_score"]),
            "MeanReversion": float(row["mean_reversion_score"]),
            "Range": float(row["range_score"]),
            "TrendContinuation": float(
                row["trend_continuation_score"]
            )
        },
        axis=1
    )

    return work[
        [
            "ticker",
            "t",
            "watch_setups"
        ]
    ].copy()

def run_watch_setup_pipeline(
    source_table,
    bars_table,
    target_table
):

    print(
        "Using github python shared utils"
    )

    (
        user,
        password,
        db,
        schema,
        host,
        port,
        engine
    ) = get_default_engine()

    sql = f"""
        SELECT
            i.ticker,
            i.t,

            i.atr_ratio,
            i.rvol,

            i.trend_regime,
            i.trend_strength,

            i.rsi_14,
            i.macd_histogram,

            i.ema20,
            i.ema50,

            b.h,
            b.l,
            b.c

        FROM raw.{source_table} i

        INNER JOIN raw.{bars_table} b
            ON i.ticker = b.ticker
        AND i.t = b.t

        WHERE i.t = (
            SELECT MAX(t)
            FROM raw.{source_table}
        )

        ORDER BY i.ticker
    """

    rows = select_to_json(
        engine,
        sql,
        params={}
    )

    if not rows:

        print(
            "No source data found"
        )

        return

    df = pd.DataFrame(
        rows
    )

    print(
        f"Rows loaded: "
        f"{len(df)}"
    )

    result_df = (
        calculate_watch_setups(
            df
        )
    )

    if result_df.empty:

        print(
            "No setup rows generated"
        )

        return

    result_df = (
        result_df[
            WATCH_SETUP_COLUMNS
        ]
        .replace(
            {
                np.nan: None
            }
        )
    )

    records = (
        result_df
        .to_dict(
            orient="records"
        )
    )

    if not records:

        print(
            "No records generated"
        )

        return

    schema_dict = (
        get_schema_dict(
            records
        )
    )

    ensure_schema_and_table(
        engine,
        "raw",
        target_table,
        schema_dict,
        None,
        False,
        False
    )

    print(
        f"Upserting "
        f"{len(records)} rows"
    )

    store_dicts_into_table(
        engine,
        records,
        "raw",
        target_table,
        upsert=True,
        ignore_keys=set(),
        use_bulk=True,
        # conflict_cols=[
        #     "ticker",
        #     "t",
        #     "watch_setup"
        # ]
        conflict_cols=[
            "ticker",
            "t"
        ]
    )

    print(
        "Finished"
    )



def run_profile_snapshot_pipeline(
    market,
    watch_setup_table,
    horizon_table,
    profile_table,
    target_table
):

    print(
        "Using github python shared utils"
    )

    (
        user,
        password,
        db,
        schema,
        host,
        port,
        engine
    ) = get_default_engine()

    watch_setup_sql = f"""
        SELECT
            ticker,
            t,
            watch_setups
        FROM raw.{watch_setup_table}
        WHERE t = (
            SELECT MAX(t)
            FROM raw.{watch_setup_table}
        )
    """

    horizon_sql = f"""
        SELECT
            ticker,
            t,
            horizons
        FROM raw.{horizon_table}
        WHERE t = (
            SELECT MAX(t)
            FROM raw.{horizon_table}
        )
    """

    profile_sql = f"""
        SELECT
            *
        FROM raw.{profile_table}
        WHERE enabled = true AND market = :market
    """

    watch_setup_rows = (
        select_to_json(
            engine,
            watch_setup_sql,
            params={}
        )
    )

    horizon_rows = (
        select_to_json(
            engine,
            horizon_sql,
            params={}
        )
    )

    profile_rows = (
        select_to_json(
            engine,
            profile_sql,
            params={"market": market}
        )
    )

    if not watch_setup_rows:

        print(
            "No watch setups found"
        )

        watch_setup_rows = []

    if not horizon_rows:

        print(
            "No horizons found"
        )

        horizon_rows = []

    if not profile_rows:

        print(
            "No profiles found"
        )

        profile_rows = []

    watch_lookup = {}

    for row in watch_setup_rows:

        watch_lookup[
            (
                row["ticker"],
                row["t"]
            )
        ] = (
            row.get(
                "watch_setups"
            )
            or {}
        )

    horizon_lookup = {}

    for row in horizon_rows:

        horizon_lookup[
            (
                row["ticker"],
                row["t"]
            )
        ] = (
            row.get(
                "horizons"
            )
            or {}
        )

    records = []

    for profile in profile_rows:

        profile_identity = (
            profile[
                "profile_identity"
            ]
        )

        profile_name = (
            profile[
                "profile_name"
            ]
        )

        allowed_horizon = (
            profile[
                "strategy_trading_horizon"
            ]
        )

        profile_horizons = (
            profile.get(
                "strategy_horizons"
            )
            or []
        )

        profile_watch_setups = (
            profile.get(
                "strategy_watch_setups"
            )
            or []
        )

        minimum_horizon_score = None

        for horizon_rule in (
            profile_horizons
        ):

            if (
                horizon_rule.get(
                    "horizon"
                )
                ==
                allowed_horizon
            ):

                minimum_horizon_score = float(
                    horizon_rule.get(
                        "minimum_score",
                        0
                    )
                )

                break

        if minimum_horizon_score is None:

            continue

        for (
            ticker,
            t
        ), watch_setups in (
            watch_lookup.items()
        ):

            horizons = (
                horizon_lookup.get(
                    (
                        ticker,
                        t
                    )
                )
            )

            if not horizons:

                continue

            horizon_score = (
                horizons.get(
                    allowed_horizon
                )
            )

            if horizon_score is None:

                continue

            horizon_score = float(
                horizon_score
            )

            if (
                horizon_score
                <
                minimum_horizon_score
            ):

                continue

            qualified_horizons = {
                allowed_horizon:
                    horizon_score
            }

            matched_watch_setups = {}

            profile_matches = True

            for watch_rule in (
                profile_watch_setups
            ):

                watch_setup_name = (
                    watch_rule.get(
                        "watch_setup"
                    )
                )

                minimum_score = float(
                    watch_rule.get(
                        "minimum_score",
                        0
                    )
                )

                actual_score = (
                    watch_setups.get(
                        watch_setup_name
                    )
                )

                if actual_score is None:

                    profile_matches = False

                    break

                actual_score = float(
                    actual_score
                )

                if (
                    actual_score
                    <
                    minimum_score
                ):

                    profile_matches = False

                    break

                matched_watch_setups[
                    watch_setup_name
                ] = actual_score

            if not profile_matches:

                continue

            snapshot_date = (
                datetime
                .fromtimestamp(
                    int(t) / 1000,
                    tz=timezone.utc
                )
                .date()
                .isoformat()
            )

            records.append(
                {
                    "ticker":
                        ticker,

                    "t":
                        int(t),

                    "snapshot_date":
                        snapshot_date,

                    "profile_identity":
                        profile_identity,

                    "profile_name":
                        profile_name,

                    "qualified_watch_setups":
                        json.dumps(
                            matched_watch_setups
                        ),

                    "qualified_horizons":
                        json.dumps(
                            qualified_horizons
                        )
                }
            )

    #
    # Tabel altijd aanmaken
    #

    schema_dict = {
        "ticker":
            "text",

        "t":
            "bigint",

        "snapshot_date":
            "text",

        "profile_identity":
            "bigint",

        "profile_name":
            "text",

        "qualified_watch_setups":
            "jsonb",

        "qualified_horizons":
            "jsonb"
    }

    ensure_schema_and_table(
        engine,
        "raw",
        target_table,
        schema_dict,
        None,
        False,
        False
    )

    if not records:

        print(
            "No profile snapshots generated"
        )

        return

    store_dicts_into_table(
        engine,
        records,
        "raw",
        target_table,
        upsert=True,
        ignore_keys=set(),
        use_bulk=True,
        conflict_cols=[
            "ticker",
            "t",
            "profile_name",
        ]
    )

    print(
        f"Stored "
        f"{len(records)} "
        f"profile snapshots"
    )



def build_run_id(
    market,
    trading_mode,
    session_scope,
    trade_day,
    session_start
):
    prefix = (
        "L"
        if trading_mode == "Live"
        else "P"
    )

    hhmm = session_start.replace(":", "")[:4]

    trade_day_str = trade_day.strftime("%Y%m%d")

    return (
        f"{prefix}_"
        f"{market.upper()}_"
        f"{session_scope.upper()}_"        
        f"{trade_day_str}_"        
        f"{hhmm}"
    )


from zoneinfo import ZoneInfo
from datetime import datetime, UTC

def get_session_window(
    engine,
    market,
    timestamp_value
):
    sql = """
    SELECT
        market_hours_sessions
    FROM raw.idts_all_reference_markets_persisted_1
    WHERE LOWER(asset_class) = LOWER(:market)
    LIMIT 1
    """

    rows = select_to_json(
        engine,
        sql,
        {
            "market": market
        }
    )

    if not rows:

        raise ValueError(
            f"No session configuration found for market '{market}'."
        )

    sessions = rows[0]["market_hours_sessions"]

    timestamp_value = int(
        timestamp_value
    )

    timestamp_utc = datetime.fromtimestamp(
        timestamp_value / 1000,
        UTC
    )

    for session in sessions:

        timezone = ZoneInfo(
            session["timezone"]
        )

        timestamp_local = (
            timestamp_utc.astimezone(
                timezone
            )
        )

        trade_day = (
            timestamp_local.date()
        )

        start_time = datetime.strptime(
            session["start"],
            "%H:%M:%S"
        ).time()

        end_time = datetime.strptime(
            session["end"],
            "%H:%M:%S"
        ).time()

        valid_from_local = datetime.combine(
            trade_day,
            start_time
        ).replace(
            tzinfo=timezone
        )

        valid_until_local = datetime.combine(
            trade_day,
            end_time
        ).replace(
            tzinfo=timezone
        )

        valid_from = int(
            valid_from_local
            .astimezone(UTC)
            .timestamp()
            * 1000
        )

        valid_until = int(
            valid_until_local
            .astimezone(UTC)
            .timestamp()
            * 1000
        )

        if (
            valid_from
            <= timestamp_value
            <= valid_until
        ):
            # return {

            #     "trade_day":
            #         trade_day,

            #     "valid_from":
            #         valid_from,

            #     "valid_until":
            #         valid_until,

            #     "session_scope":
            #         session["session_scope"]
            # }

            return {

                "trade_day":
                    trade_day,

                "valid_from":
                    valid_from,

                "valid_until":
                    valid_until,

                "session_scope":
                    session["session_scope"],

                "session_start":
                    session["start"]
            }

    raise ValueError(
        f"No matching session found for "
        f"market={market} "
        f"timestamp={timestamp_value}"
    )

def get_or_create_trading_session(
    engine,
    target_schema_name,
    target_table,
    market,
    trading_mode,
    timestamp_value
):

    session_window = get_session_window(
        engine,
        market,
        timestamp_value
    )

    valid_from = session_window["valid_from"]
    valid_until = session_window["valid_until"]
    session_scope = session_window["session_scope"]

    existing_sql = f"""
    SELECT *
    FROM {target_schema_name}.{target_table}
    WHERE
        market = :market
        AND trading_mode = :trading_mode
        AND valid_from = :valid_from
        AND valid_until = :valid_until
        AND session_scope = :session_scope
    LIMIT 1
    """

    try:

        existing_rows = select_to_json(
            engine,
            existing_sql,
            {
                "market": market,
                "trading_mode": trading_mode,
                "valid_from": valid_from,
                "valid_until": valid_until,
                "session_scope": session_scope
            }
        )

    except Exception:

        existing_rows = []

    if existing_rows:

        existing_rows[0]["is_new"] = False

        return existing_rows[0]

    record = {

        "market":
            market,

        "run_id":
            build_run_id(
                market,
                trading_mode,
                session_scope,
                session_window["trade_day"],
                session_window["session_start"],
            ),

        "trading_mode":
            trading_mode,

        "valid_from":
            valid_from,

        "valid_until":
            valid_until,

        "session_scope":
            session_scope,

        "created_at":
            int(
                datetime.now(
                    UTC
                ).timestamp()
                * 1000
            )
    }

    schema_dict = get_schema_dict(
        [record]
    )

    ensure_schema_and_table(
        engine,
        target_schema_name,
        target_table,
        schema_dict,
        None,
        False,
        False
    )

    store_dicts_into_table(
        engine,
        [record],
        target_schema_name,
        target_table,
        upsert=False,
        ignore_keys=set(),
        use_bulk=True,
        conflict_cols=[]
    )

    record["is_new"] = True

    return record

def get_profile_configuration(
    engine,
    profile_name
):
    sql = """
    SELECT
        p.profile_identity,
        p.trading_mode,
        p.market,
        p.strategy_trading_side,
        p.strategy_trading_horizon,
        r.*

    FROM raw.idts_all_application_profiles_persisted_1 p

    INNER JOIN raw.idts_all_application_riskreward_persisted_1 r
        ON p.profile_name = r.profile_name

    WHERE p.profile_name = :profile_name
      AND p.enabled = true
      AND r.enabled = true
    """

    rows = select_to_json(
        engine,
        sql,
        {
            "profile_name": profile_name
        }
    )

    if not rows:
        return None

    return rows

 
def get_profile_account(
    engine,
    profile_name
):
    sql = """
    SELECT
        p.profile_identity,
        p.trading_mode,
        p.market,
        p.strategy_trading_side,
        p.strategy_trading_horizon,
        p.strategy_minimum_trend_strength,
        p.strategy_minimum_traded_volume,
        p.strategy_minimum_relative_volume,
        p.strategy_minimum_volume_weighted_price,
        p.strategy_minimum_signal_strength,
        p.strategy_position_management_trading_capital,
        p.strategy_position_management_max_concurrent_trades,
        p.strategy_position_management_max_trades_per_ticker,
        p.strategy_position_management_max_trades_per_day,
        p.strategy_position_management_min_correlation_group_threshold,
        p.strategy_position_management_max_correlation_group_strength,
        p.strategy_position_management_max_trades_per_correlation_group,
        p.strategy_session_scopes,
        p.strategy_holding_policy_min_holding_period,
        p.strategy_holding_policy_min_holding_unit,
        p.strategy_holding_policy_max_holding_period,
        p.strategy_holding_policy_max_holding_unit,            
        a.*

    FROM raw.idts_all_application_profiles_persisted_1 p

    INNER JOIN raw.idts_all_application_accounts_persisted_1 a
        ON p.profile_name = a.profile_name

    WHERE p.profile_name = :profile_name
      AND p.enabled = true
      AND a.enabled = true

    LIMIT 1
    """

    rows = select_to_json(
        engine,
        sql,
        {
            "profile_name": profile_name
        }
    )

    if not rows:
        return None

    return rows[0]

def get_broker_symbol_mapping(
    engine,
    broker_name,
    account_mode,
    ticker,
    position_side,
):
    sql = """
    SELECT symbol
    FROM raw.idts_all_reference_brokersymbols_persisted_1
    WHERE broker_name = :broker_name
      AND account_mode = :account_mode
      AND ticker = :ticker
      AND position_side = :position_side
      AND enabled = true
    LIMIT 1
    """

    rows = select_to_json(
        engine,
        sql,
        {
            "broker_name": broker_name,
            "account_mode": account_mode,
            "ticker": ticker,
            "position_side": position_side,
        }
    )

    if not rows:
        return None

    return rows[0]["symbol"]

def get_symbol_for_ticker(
    engine,
    broker_name,
    account_mode,
    ticker,
    position_side
):
    original_ticker = ticker

    sql = """
    SELECT
        asset_class,
        asset_long_format,
        asset_short_format
    FROM raw.idts_all_application_accounts_persisted_1
    WHERE broker_name = :broker_name
      AND account_mode = :account_mode
    LIMIT 1
    """

    rows = select_to_json(
        engine,
        sql,
        {
            "broker_name": broker_name,
            "account_mode": account_mode
        }
    )

    if not rows:
        return get_broker_symbol_mapping(
            engine,
            broker_name,
            account_mode,
            original_ticker,
            position_side,
        )

    account = rows[0]

    asset_class = (
        account.get("asset_class")
        or ""
    )

    symbol_format = (
        account["asset_long_format"]
        if position_side == "Long"
        else account["asset_short_format"]
    )

    #
    # Stocks
    #
    if asset_class.lower() == "stocks":

        symbol = ticker

        sql = """
        SELECT 1
        FROM raw.alpaca_stocks_market_tickers_persisted_1
        WHERE symbol = :symbol
        LIMIT 1
        """

        rows = select_to_json(
            engine,
            sql,
            {
                "symbol": symbol
            }
        )

        if rows:
            return symbol

        return get_broker_symbol_mapping(
            engine,
            broker_name,
            account_mode,
            original_ticker,
            position_side,
        )

    #
    # Crypto
    #
    if ":" in ticker:
        ticker = ticker.split(":", 1)[1]

    match = re.match(
        r"^([A-Z]+)(USD|USDT|USDC|EUR)$",
        ticker
    )

    if not match:
        return get_broker_symbol_mapping(
            engine,
            broker_name,
            account_mode,
            original_ticker,
            position_side,
        )

    base_asset = match.group(1)
    quote = match.group(2)

    symbol = (
        symbol_format
        .replace("{base_asset}", base_asset)
        .replace("{quote}", quote)
    )

    if broker_name == "Kraken":

        sql = """
        SELECT 1
        FROM raw.kraken_crypto_market_tickers_persisted_1
        WHERE symbol = :symbol
        LIMIT 1
        """

    elif broker_name == "OKX":

        sql = """
        SELECT 1
        FROM raw.okx_crypto_market_tickers_persisted_1
        WHERE inst_id = :symbol
        LIMIT 1
        """

    else:
        return symbol

    rows = select_to_json(
        engine,
        sql,
        {
            "symbol": symbol
        }
    )

    if rows:
        return symbol

    return get_broker_symbol_mapping(
        engine,
        broker_name,
        account_mode,
        original_ticker,
        position_side,
    )


def get_positions_for_symbol(
    engine,
    market,
    broker_name,
    profile_identity,
    account_mode,
    symbol,
):
    sql = """
    SELECT *
    FROM raw.vw_idts_all_market_positions_snapshotted_1
    WHERE market = :market
      AND broker_name = :broker_name
      AND profile_identity = :profile_identity
      AND account_mode = :account_mode
      AND symbol = :symbol
    """

    rows = select_to_json(
        engine,
        sql,
        {
            "market": market,
            "broker_name": broker_name,
            "profile_identity": profile_identity,
            "account_mode": account_mode,
            "symbol": symbol,
        }
    )

    return rows or []

def get_positions_for_profile(
    engine,
    market,
    broker_name,
    profile_identity,
    account_mode,
):
    sql = """
    SELECT *

    FROM raw.vw_idts_all_market_positions_snapshotted_1

    WHERE market = :market
      AND broker_name = :broker_name
      AND profile_identity = :profile_identity
      AND account_mode = :account_mode
    """

    rows = select_to_json(
        engine,
        sql,
        {
            "market": market,
            "broker_name": broker_name,
            "profile_identity": profile_identity,
            "account_mode": account_mode,
        }
    )

    return rows or []


def build_profile_dict(
    row
):

    return {

        "profile_name":
            row["profile_name"],

        "profile_identity":
            row["profile_identity"],

        "market":
            row["market"],

        "trading_mode":
            row["trading_mode"],

        "rule_engine_version":
            row["rule_engine_version"],

        "strategy_trading_horizon":
            row["strategy_trading_horizon"],

        "strategy_trading_side":
            row["strategy_trading_side"],

        "strategy_minimum_trend_strength":
            row["strategy_minimum_trend_strength"],

        "strategy_minimum_traded_volume":
            row["strategy_minimum_traded_volume"],

        "strategy_minimum_relative_volume":
            row["strategy_minimum_relative_volume"],

        "strategy_minimum_volume_weighted_price":
            row["strategy_minimum_volume_weighted_price"],
    
        "strategy_minimum_signal_strength":
            row["strategy_minimum_signal_strength"]
    }


def load_engine_configuration(
    engine,
    table_name: str,
    engine_version: int
):

    query = text(
        f"""
        SELECT
            provider_name,
            provider_version
        FROM
            {table_name}
        WHERE
            engine_version = :engine_version
        ORDER BY
            sort_order
        """
    )

    with engine.connect() as connection:

        result = connection.execute(
            query,
            {
                "engine_version": engine_version
            }
        )

        configuration = [
            (
                row.provider_name,
                row.provider_version
            )
            for row in result
        ]

    return (
        configuration
        if configuration
        else None
    )


def append_signal_score_rows(
    records,
    result,
    profile_row,
    ticker,
    timestamp_value,
    run_id,
    provider_count_configured,
    provider_count_evaluated,
    providers_evaluated_json,
    providers_not_evaluated_json
):

    signal_summary = (
        result.get(
            "signal_summary",
            {}
        )
    )

    rule_engine_version = (
        profile_row[
            "rule_engine_version"
        ]
    )

    for side, signals in (
        signal_summary.items()
    ):

        for signal_name, percentage in (
            signals.items()
        ):

            if signal_name not in [
                "buy_percentage",
                "wait_percentage",
                "hold_percentage",
                "sell_percentage"
            ]:
                continue

            signal = (
                signal_name
                .replace(
                    "_percentage",
                    ""
                )
                # .upper()
            )

            records.append({

                "run_id":
                    run_id,

                "profile_identity":
                    profile_row[
                        "profile_identity"
                    ],

                "profile_name":
                    profile_row[
                        "profile_name"
                    ],

                "trading_mode":
                    profile_row[
                        "trading_mode"
                    ],

                "ticker":
                    ticker,

                "t":
                    timestamp_value,

                "rule_engine_version":
                    rule_engine_version,

                "side":
                    # side.upper(),
                    side.title(),

                "signal":
                    signal.title(),

                "percentage":
                    percentage,

                "provider_count_configured":
                    provider_count_configured,
                "provider_count_evaluated":
                    provider_count_evaluated,

                "providers_evaluated_json":
                    providers_evaluated_json,
                "providers_not_evaluated_json":
                    providers_not_evaluated_json,                    
            })

def append_provider_score_rows(
    records,
    result,
    profile_row,
    ticker,
    timestamp_value,
    run_id
):

    trading_signals = (
        result.get(
            "trading_signals",
            []
        )
    )

    rule_engine_version = (
        profile_row[
            "rule_engine_version"
        ]
    )

    for signal in trading_signals:

        records.append({
            "run_id":
                run_id,

            "profile_identity":
                profile_row[
                    "profile_identity"
                ],

            "profile_name":
                profile_row[
                    "profile_name"
                ],

            "trading_mode":
                profile_row[
                    "trading_mode"
                ],

            "ticker":
                ticker,

            "t":
                timestamp_value,

            "rule_engine_version":
                rule_engine_version,

            "provider":
                signal.get(
                    "provider"
                ),

            "provider_version":
                signal.get(
                    "provider_version"
                ),

            "side":
                str(
                    signal.get(
                        "side"
                    )
                # ).upper(),
                ),

            "signal":
                str(
                    signal.get(
                        "signal"
                    )
                # ).upper(),
                ),

            "confidence_percentage":
                signal.get(
                    "confidence_percentage"
                ),

            "validations_json":
                json.dumps(
                    signal.get(
                        "validations",
                        []
                    )
                )
        })


def append_watch_setup_row(
    records,
    profile_row,
    timestamp_value,
    watch_setup_keys
):

    key = (

        profile_row[
            "profile_identity"
        ],

        profile_row[
            "broker_name"
        ],

        profile_row[
            "account_mode"
        ],

        profile_row[
            "rule_engine_version"
        ],

        profile_row[
            "strategy_trading_horizon"
        ],

        profile_row[
            "strategy_trading_side"
        ]
    )

    if key in watch_setup_keys:

        return

    watch_setup_keys.add(
        key
    )

    records.append({


        "t":
            timestamp_value,

        "profile_identity":
            profile_row[
                "profile_identity"
            ],

        "profile_name":
            profile_row[
                "profile_name"
            ],

        "trading_mode":
            profile_row[
                "trading_mode"
            ],

        "broker_name":
            profile_row[
                "broker_name"
            ],

        "account_mode":
            profile_row[
                "account_mode"
            ],

        "secrets":
            profile_row[
                "secrets"
            ],

        "rule_engine_version":
            profile_row[
                "rule_engine_version"
            ],

        "strategy_trading_horizon":
            profile_row[
                "strategy_trading_horizon"
            ],

        "trading_side":
            profile_row[
                "strategy_trading_side"
            ],

        "strategy_minimum_trend_strength":
            profile_row[
                "strategy_minimum_trend_strength"
            ],

        "strategy_minimum_traded_volume":
            profile_row[
                "strategy_minimum_traded_volume"
            ],

        "strategy_minimum_relative_volume":
            profile_row[
                "strategy_minimum_relative_volume"
            ],

        "strategy_minimum_volume_weighted_price":
            profile_row[
                "strategy_minimum_volume_weighted_price"
            ],

        "strategy_minimum_signal_strength":
            profile_row[
                "strategy_minimum_signal_strength"
            ]
    })


def calculate_risk_reward_ratio(
    risk_reward_notation: str
):
    risk, reward = map(
        float,
        risk_reward_notation.split(":")
    )

    risk_reward_ratio = reward / risk

    return (
        risk,
        reward,
        risk_reward_ratio
    )



from math import floor

def calculate_standard_position_size(
    starting_capital,
    max_risk_per_trade_percentage,
    max_concurrent_trades,
    atr,
    atr_multiplier,
    entry
):
    if (
        atr <= 0
        or atr_multiplier <= 0
        or entry <= 0
        or max_concurrent_trades <= 0
    ):
        return 0, 0

    capital_per_trade = (
        starting_capital /
        max_concurrent_trades
    )

    max_risk_per_trade = (
        capital_per_trade *
        (
            max_risk_per_trade_percentage / 100
        )
    )

    stop_loss_distance = (
        atr * atr_multiplier
    )

    # standard_size = floor(
    #     max_risk_per_trade /
    #     stop_loss_distance
    # )

    risk_size = floor(
        max_risk_per_trade /
        stop_loss_distance
    )

    capital_size = floor(
        capital_per_trade /
        entry
    )

    standard_size = min(
        risk_size,
        capital_size
    )

    standard_capital = (
        standard_size *
        entry
    )

    return (
        standard_size,
        standard_capital
    )


def calculate_kelly_position_size(
    starting_capital,
    risk_reward_ratio,
    expected_win_rate,
    fractional_kelly,
    entry
):


    if (
        risk_reward_ratio <= 0
        or entry <= 0
        or expected_win_rate < 0
        or expected_win_rate > 1
    ):
        return 0, 0

    kelly = (
        expected_win_rate -
        (
            (1 - expected_win_rate)
            / risk_reward_ratio
        )
    )

    fractional_kelly_position = (
        kelly *
        fractional_kelly
    )

    kelly_capital = (
        starting_capital *
        fractional_kelly_position
    )

    kelly_size = floor(
        kelly_capital /
        entry
    )

    return kelly_size, kelly_capital


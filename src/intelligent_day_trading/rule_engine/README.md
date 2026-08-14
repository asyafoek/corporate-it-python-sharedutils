# GEX like comparison for other markets

## Compare GEX with rule providers
| GEX Concept | Waar kijkt GEX naar? | Jouw OHLCV / Indicator equivalent | Jouw provider(s) |
|------------|----------------------|-----------------------------------|------------------|
| Positive Gamma | Range-bound markt, prijs wordt teruggetrokken naar evenwicht | Lage ADX, lage ATR, lage RVOL, trend_regime=RANGING | range, mean_reversion, volatility |
| Negative Gamma | Trendmarkt, bewegingen worden versterkt | Hoge ADX, stijgende ATR, hoge RVOL, trend_regime=TRENDING | breakout, momentum, trend_following, volatility |
| Gamma Flip | Omslag van range naar trend of andersom | ADX stijgt, ATR stijgt, RVOL stijgt | breakout, momentum, volatility |
| Call Wall | Sterke weerstand waar prijs blijft hangen | resistance_upper, resistance_lower | range, breakout, reversal |
| Put Wall | Sterke support waar prijs blijft hangen | support_upper, support_lower | range, mean_reversion, reversal |
| Volatility Suppression | Lage volatiliteit en weinig beweging | Lage ATR, lage RVOL | volatility, range |
| Volatility Expansion | Toenemende volatiliteit en grotere candles | Hoge ATR, hoge RVOL | volatility, breakout, momentum |
| Dealer Hedging Mean Reversion | Markt trekt terug naar gemiddelde | Support/Resistance + lage ADX | mean_reversion, range |
| Dealer Hedging Trend Amplification | Trends worden sterker | Hoge ADX + hoge RVOL | breakout, trend_following, momentum |
| Market Regime | Trend versus range omgeving | trend_regime, volatility_regime, ticker_regime | volatility, range, trend_following |
| Market Participation | Hoeveel partijen actief zijn | RVOL, volume (v) | volatility, momentum, breakout |
| Fair Value Magnet | Prijs blijft rond evenwicht hangen | VWAP (vw) | mean_reversion, range |



## Compare GEX with market regimes
| GEX-omgeving            | Jouw regime                              |
|-------------------------|-------------------------------------------|
| Positive Gamma          | Sideways + Quiet                          |
| Positive Gamma Extreme  | Sideways + Quiet met lage RVOL            |
| Negative Gamma          | Bullish/Bearish + Volatile                |
| Gamma Flip              | Overgang Sideways → Bullish/Bearish + Volatile |
| Volatility Expansion    | Bullish/Bearish + Volatile                |
| Volatility Suppression  | Sideways + Quiet                          |

## Backtest provider performance per market regime for GEX like solution
| Provider         | Market | Regime            | Win Rate | Profit Factor |
|-----------------|---------|-------------------|----------|---------------|
| momentum        | stocks  | bullish volatile  | 74%      | 2.2 |
| momentum        | crypto  | bullish volatile  | 61%      | 1.3 |
| range           | stocks  | sideways quiet    | 79%      | 2.5 |
| breakout        | crypto  | sideways quiet    | 34%      | 0.6 | 

## Uitleg profile loss  calculation
``` remark 
Profit Factor = Totale Winst / Totale Verlies
```

## Profit Factor

Profit Factor meet hoeveel winst een strategie of provider maakt ten opzichte van het totale verlies.

### Formule

```text
Profit Factor = Totale Winst / Totale Verlies
```

### Voorbeeld

Trades:

```text
+2%
+3%
-1%
+4%
-2%
```

Berekening:

```text
Totale Winst   = 2 + 3 + 4 = 9

Totale Verlies = 1 + 2 = 3

Profit Factor = 9 / 3 = 3.0
```

### Interpretatie

```text
PF < 1.0  = Verlieslatend
PF = 1.0  = Break-even
PF > 1.5  = Goed
PF > 2.0  = Sterk
PF > 3.0  = Uitstekend
```

### Toepassing Op Providers

Meet Profit Factor per combinatie van:

- Market
- Trend Regime
- Volatility Regime
- Provider
- Side

Voorbeeld:

```text
Market            : Crypto
Trend Regime      : Bullish
Volatility Regime : Volatile
Provider          : Momentum
Side              : Long

Signals           : 1,250
Win Rate          : 73.5%
Average Return    : 1.8%
Profit Factor     : 2.1
```

### Waarom Belangrijk?

Win Rate alleen vertelt niet het hele verhaal.

Voorbeeld:

```text
Win Rate = 40%

+10%
+8%
-1%
-1%
-1%
```

Dan:

```text
Totale Winst   = 18
Totale Verlies = 3

Profit Factor = 6.0
```

Ondanks een lage Win Rate is de provider zeer winstgevend.

Daarom is Profit Factor vaak een betere kwaliteitsmetric dan alleen Win Rate.



# Profit Factor ranges to qualify setup

## Definitie

Profit Factor meet hoeveel winst een strategie, provider of signal produceert ten opzichte van het totale verlies.

## Formule

```text
Profit Factor = Totale Winst / Totale Verlies
```

## Voorbeeld

Returns:

```text
+2.0%
+3.0%
-1.0%
+4.0%
-2.0%
```

Berekening:

```text
Totale Winst   = 2 + 3 + 4 = 9

Totale Verlies = 1 + 2 = 3

Profit Factor  = 9 / 3 = 3.0
```

## Interpretatie

| Profit Factor | Betekenis |
|--------------|-----------|
| < 1.0 | Verlieslatend |
| = 1.0 | Break-even |
| > 1.5 | Goed |
| > 2.0 | Sterk |
| > 3.0 | Uitstekend |

## Waarom Niet Alleen Win Rate?

### Strategie A

```text
+10%
+8%
-1%
-1%
-1%
```

```text
Win Rate
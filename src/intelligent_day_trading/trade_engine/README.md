Samenvatting voor de geautomatiseerde AI test strategie: 
- Optimaliseren rule providers en beslissingen kan via backtests zijn nadat een opportunity of signal bestaat
- Bepalen welke tickers überhaupt in de pipeline komen moeten via live shadow/paper trading gevalideerd worden. Dat is eigenlijk een gezonde scheiding tussen research en discovery.

* Workload Market Data -> Websocket
    Collect and normalize real-time market data from exchanges/providers.
    1min bars
    ↓
Kafka: market-data-received -> dev.corporate-it.raw.massive_crypto.ohlvc_1min.sourced.1, dev.corporate-it.raw.massive_stocks.ohlvc_1min.sourced.1
    ↓
* Workload Watchlist Check (Crypto, Stocks Quality Engine)
    Determine whether an asset is eligible for further analysis based on watchlists, liquidity, volume, quality rules, market status, etc.
    Determine per ticker the market regime 6 per market every 15minutes
    Using same rule engine of 12 provider but on 15min bars
    Using profile with thresholds to filter strength
    Using profile market regimes which market regimes to use for trading
    ↓
Kafka: watchlist-checked -> dev.corporate-it.processed.idts_trade.opportunity.detected.1
    ↓
* Workload Signal Evaluation (Signal Engine)
    Apply trading strategy logic and generate Buy/Sell/Hold signals.
    Using same rule engine of 12 provider but on realtime 1min bars
    ↓
Kafka: trade-signals-generated -> dev.corporate-it.processed.idts_trade.signal.determined.1
    ↓
* Workload Risk Management (Risk Engine)
    Kelly Criterion, Position sizing, stop loss calculation, exposure limits, portfolio checks, risk approval/rejection.
    ↓
Kafka: risk-decisions-made -> dev.corporate-it.processed.idts_trade.risk.assesed.1
    ↓
* Workload Order & Execution (Order Engine)
    Create orders, route to broker, track execution status and fill details.    
    Spread, Fees en slippage op het moment dat je een order uitvoert, niet bij het genereren van het signaal.
    - Order aanmaken
    - Fill price bepalen
    - Spread toepassen13
    - Slippage toepassen
    - Fees/commission toepassen
    - Executie registreren
    ↓
Kafka: trade-outcomes-recorded -> dev.corporate-it.processed.idts_trade.order.executed.1
    ↓
* Workload Read Broker Order Status, elke 5minuten
    Receive fills, cancellations, rejections, partial executions.



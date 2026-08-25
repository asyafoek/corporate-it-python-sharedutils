Market Data -> Websocket
    ↓
Kafka: market-data-received -> dev.corporate-it.raw.massive_crypto.ohlvc_1min.sourced.1, dev.corporate-it.raw.massive_stocks.ohlvc_1min.sourced.1
    ↓
Workload Watchlist Check (Crypto, Stocks Quality Engine)
    ↓
Kafka: watchlist-checked -> dev.corporate-it.processed.idts_trade.opportunity.detected.1
    ↓
Workload Signal Evaluation (Signal Engine)
    ↓
Kafka: trade-signals-generated -> dev.corporate-it.processed.idts_trade.signal.determined.1
    ↓
Workload Risk Management (Risk Engine)
    ↓
Kafka: risk-decisions-made -> dev.corporate-it.processed.idts_trade.risk.assesed.1
    ↓
Workload Order & Execution (Order Engine)
    ↓
Kafka: trade-outcomes-recorded -> dev.corporate-it.processed.idts_trade.order.executed.1
    ↓
Broker Receive Order Status



def get_topics():
    topic_list = [
    'dev.corporate-it.landing.massive_crypto.ohlvc_custom.sourced.1', 
    'dev.corporate-it.landing.massive_stocks.ohlvc_custom.sourced.1', 
    'dev.corporate-it.processed.massive_crypto.ohlvc_custom.finalized.1', 
    'dev.corporate-it.processed.massive_stocks.ohlvc_custom.finalized.1', 
    ]
    return topic_list

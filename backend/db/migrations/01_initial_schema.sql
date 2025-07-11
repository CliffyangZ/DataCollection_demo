-- 1. 創建數據庫和擴展
-- CREATE DATABASE crypto_trading;
-- \c crypto_trading;

-- 啟用 TimescaleDB 擴展
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 2. 創建交易對資訊表（維度表）
CREATE TABLE trading_pairs (
    pair_id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    base_currency VARCHAR(10) NOT NULL,
    quote_currency VARCHAR(10) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    min_trade_size DECIMAL(20,8),
    max_trade_size DECIMAL(20,8),
    tick_size DECIMAL(20,8),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 創建市場數據表（時間序列表）
CREATE TABLE market_data (
    time TIMESTAMPTZ NOT NULL,
    pair_id INTEGER NOT NULL REFERENCES trading_pairs(pair_id),
    open DECIMAL(20,8) NOT NULL,
    high DECIMAL(20,8) NOT NULL,
    low DECIMAL(20,8) NOT NULL,
    close DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8) NOT NULL,
    quote_volume DECIMAL(20,8),
    trade_count INTEGER,
    PRIMARY KEY (time, pair_id)
);

-- 轉換為 Hypertable
SELECT create_hypertable('market_data', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- 4. 創建交易記錄表（時間序列表）
CREATE TABLE trades (
    time TIMESTAMPTZ NOT NULL,
    trade_id BIGINT NOT NULL,
    pair_id INTEGER NOT NULL REFERENCES trading_pairs(pair_id),
    price DECIMAL(20,8) NOT NULL,
    quantity DECIMAL(20,8) NOT NULL,
    side VARCHAR(4) NOT NULL CHECK (side IN ('buy', 'sell')),
    maker_order_id BIGINT,
    taker_order_id BIGINT,
    PRIMARY KEY (time, trade_id, pair_id)
);

-- 轉換為 Hypertable
SELECT create_hypertable('trades', 'time',
    chunk_time_interval => INTERVAL '6 hours',
    if_not_exists => TRUE
);

-- 5. 創建訂單簿快照表（時間序列表）
CREATE TABLE orderbook_snapshots (
    time TIMESTAMPTZ NOT NULL,
    pair_id INTEGER NOT NULL REFERENCES trading_pairs(pair_id),
    sequence_id BIGINT NOT NULL,
    bids JSONB NOT NULL,
    asks JSONB NOT NULL,
    PRIMARY KEY (time, pair_id, sequence_id)
);

-- 轉換為 Hypertable
SELECT create_hypertable('orderbook_snapshots', 'time',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- 6. 創建技術指標表（時間序列表）
CREATE TABLE technical_indicators (
    time TIMESTAMPTZ NOT NULL,
    pair_id INTEGER NOT NULL REFERENCES trading_pairs(pair_id),
    timeframe VARCHAR(10) NOT NULL,
    indicator_name VARCHAR(50) NOT NULL,
    indicator_value JSONB NOT NULL,
    PRIMARY KEY (time, pair_id, timeframe, indicator_name)
);

-- 轉換為 Hypertable
SELECT create_hypertable('technical_indicators', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);
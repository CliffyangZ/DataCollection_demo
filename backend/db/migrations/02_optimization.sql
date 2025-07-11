-- ========================================
-- 1. 索引優化策略
-- ========================================

-- 市場數據表索引
CREATE INDEX idx_market_data_pair_time ON market_data(pair_id, time DESC);
CREATE INDEX idx_market_data_volume ON market_data(volume) WHERE volume > 0;

-- 交易記錄表索引
CREATE INDEX idx_trades_pair_time ON trades(pair_id, time DESC);
CREATE INDEX idx_trades_price ON trades(price);
CREATE INDEX idx_trades_side ON trades(side);

-- 訂單簿快照表索引
CREATE INDEX idx_orderbook_pair_time ON orderbook_snapshots(pair_id, time DESC);

-- 技術指標表索引
CREATE INDEX idx_indicators_pair_timeframe ON technical_indicators(pair_id, timeframe, time DESC);
CREATE INDEX idx_indicators_name ON technical_indicators(indicator_name);

-- ========================================
-- 2. 壓縮策略
-- ========================================

-- 啟用自動壓縮（7天後的數據）
ALTER TABLE market_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'pair_id',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('market_data', INTERVAL '7 days');

-- 交易記錄壓縮
ALTER TABLE trades SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'pair_id',
    timescaledb.compress_orderby = 'time DESC, trade_id'
);

SELECT add_compression_policy('trades', INTERVAL '3 days');

-- ========================================
-- 3. 連續聚合視圖
-- ========================================

-- 1分鐘 K線聚合
CREATE MATERIALIZED VIEW market_data_1m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS bucket,
    pair_id,
    FIRST(open, time) AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    LAST(close, time) AS close,
    SUM(volume) AS volume,
    SUM(quote_volume) AS quote_volume,
    SUM(trade_count) AS trade_count
FROM market_data
GROUP BY bucket, pair_id
WITH NO DATA;

-- 設置連續聚合刷新策略
SELECT add_continuous_aggregate_policy('market_data_1m',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute');

-- 5分鐘 K線聚合
CREATE MATERIALIZED VIEW market_data_5m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('5 minutes', time) AS bucket,
    pair_id,
    FIRST(open, time) AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    LAST(close, time) AS close,
    SUM(volume) AS volume,
    SUM(quote_volume) AS quote_volume,
    SUM(trade_count) AS trade_count
FROM market_data
GROUP BY bucket, pair_id
WITH NO DATA;

-- 1小時 K線聚合
CREATE MATERIALIZED VIEW market_data_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    pair_id,
    FIRST(open, time) AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    LAST(close, time) AS close,
    SUM(volume) AS volume,
    SUM(quote_volume) AS quote_volume,
    SUM(trade_count) AS trade_count
FROM market_data
GROUP BY bucket, pair_id
WITH NO DATA;

-- ========================================
-- 4. 數據保留策略
-- ========================================

-- 設置數據保留策略（保留5年數據）
SELECT add_retention_policy('trades', INTERVAL '5 year');
SELECT add_retention_policy('orderbook_snapshots', INTERVAL '30 days');

-- ========================================
-- 5. 查詢優化函數
-- ========================================

-- 獲取最新價格函數
CREATE OR REPLACE FUNCTION get_latest_price(p_pair_id INTEGER)
RETURNS TABLE(
    pair_id INTEGER,
    price DECIMAL(20,8),
    volume DECIMAL(20,8),
    time TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        md.pair_id,
        md.close as price,
        md.volume,
        md.time
    FROM market_data md
    WHERE md.pair_id = p_pair_id
    ORDER BY md.time DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- 獲取價格變化統計
CREATE OR REPLACE FUNCTION get_price_stats(
    p_pair_id INTEGER,
    p_interval INTERVAL DEFAULT '24 hours'
)
RETURNS TABLE(
    high_price DECIMAL(20,8),
    low_price DECIMAL(20,8),
    avg_price DECIMAL(20,8),
    total_volume DECIMAL(20,8),
    price_change DECIMAL(20,8),
    price_change_pct DECIMAL(10,4)
) AS $$
BEGIN
    RETURN QUERY
    WITH price_range AS (
        SELECT
            MAX(high) AS high_price,
            MIN(low) AS low_price,
            AVG(close) AS avg_price,
            SUM(volume) AS total_volume,
            FIRST(open, time) AS first_open,
            LAST(close, time) AS last_close
        FROM market_data
        WHERE pair_id = p_pair_id
            AND time >= NOW() - p_interval
    )
    SELECT
        pr.high_price,
        pr.low_price,
        pr.avg_price,
        pr.total_volume,
        pr.last_close - pr.first_open AS price_change,
        ((pr.last_close - pr.first_open) / pr.first_open * 100)::DECIMAL(10,4) AS price_change_pct
    FROM price_range pr;
END;
$$ LANGUAGE plpgsql;
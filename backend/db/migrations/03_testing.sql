-- ========================================
-- 測試數據插入和查詢
-- ========================================

-- 1. 插入測試交易對
INSERT INTO trading_pairs (symbol, base_currency, quote_currency, exchange, min_trade_size, max_trade_size, tick_size)
VALUES
    ('BTC/USDT', 'BTC', 'USDT', 'Binance', 0.00001, 10000, 0.01),
    ('ETH/USDT', 'ETH', 'USDT', 'Binance', 0.0001, 10000, 0.01),
    ('BNB/USDT', 'BNB', 'USDT', 'Binance', 0.001, 10000, 0.01);

-- 2. 生成測試市場數據
INSERT INTO market_data (time, pair_id, open, high, low, close, volume, quote_volume, trade_count)
SELECT
    generate_series(
        NOW() - INTERVAL '7 days',
        NOW(),
        INTERVAL '1 minute'
    ) AS time,
    1 AS pair_id,  -- BTC/USDT
    40000 + random() * 5000 AS open,
    40000 + random() * 5500 AS high,
    40000 + random() * 4500 AS low,
    40000 + random() * 5000 AS close,
    random() * 100 AS volume,
    random() * 4500000 AS quote_volume,
    (random() * 1000)::INTEGER AS trade_count;

-- 3. 性能測試查詢

-- 測試1: 獲取最新價格（應該在毫秒級）
EXPLAIN ANALYZE
SELECT * FROM get_latest_price(1);

-- 測試2: 獲取24小時統計（應該在10ms內）
EXPLAIN ANALYZE
SELECT * FROM get_price_stats(1, '24 hours');

-- 測試3: 時間範圍查詢（使用索引）
EXPLAIN ANALYZE
SELECT time, close, volume
FROM market_data
WHERE pair_id = 1
    AND time >= NOW() - INTERVAL '1 hour'
ORDER BY time DESC;

-- 測試4: 聚合查詢性能
EXPLAIN ANALYZE
SELECT
    time_bucket('5 minutes', time) AS bucket,
    AVG(close) AS avg_price,
    SUM(volume) AS total_volume
FROM market_data
WHERE pair_id = 1
    AND time >= NOW() - INTERVAL '24 hours'
GROUP BY bucket
ORDER BY bucket DESC;

-- 4. 驗證數據完整性

-- 檢查數據連續性
WITH time_gaps AS (
    SELECT
        time,
        LAG(time) OVER (ORDER BY time) AS prev_time,
        time - LAG(time) OVER (ORDER BY time) AS gap
    FROM market_data
    WHERE pair_id = 1
        AND time >= NOW() - INTERVAL '1 hour'
)
SELECT COUNT(*) AS gap_count
FROM time_gaps
WHERE gap > INTERVAL '2 minutes';

-- 檢查數據異常值
SELECT COUNT(*) AS anomaly_count
FROM market_data
WHERE pair_id = 1
    AND (high < low OR open < 0 OR close < 0 OR volume < 0);

-- 5. 壓縮效果驗證

-- 查看壓縮前後大小對比
SELECT
    hypertable_name,
    before_compression_total_bytes / 1024 / 1024 AS before_mb,
    after_compression_total_bytes / 1024 / 1024 AS after_mb,
    (1 - after_compression_total_bytes::FLOAT / before_compression_total_bytes) * 100 AS compression_ratio
FROM timescaledb_information.compression_stats
WHERE hypertable_name IN ('market_data', 'trades');

-- ========================================
-- 監控查詢
-- ========================================

-- 查看 Hypertable 狀態
SELECT
    hypertable_name,
    num_chunks,
    compressed_chunk_count,
    total_size,
    compressed_size
FROM timescaledb_information.hypertable;

-- 查看連續聚合狀態
SELECT
    view_name,
    materialization_hypertable_name,
    refresh_lag,
    max_interval_per_job
FROM timescaledb_information.continuous_aggregates;
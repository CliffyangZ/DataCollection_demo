"""
虛擬貨幣交易數據庫訪問層
"""
import asyncio
import asyncpg
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from contextlib import asynccontextmanager

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataAccess:
    """虛擬貨幣數據庫訪問類"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """初始化數據庫連接池"""
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=10,
            max_size=20,
            command_timeout=60
        )
        logger.info("數據庫連接池已初始化")

    async def close(self):
        """關閉數據庫連接池"""
        if self.pool:
            await self.pool.close()
            logger.info("數據庫連接池已關閉")

    @asynccontextmanager
    async def acquire(self):
        """獲取數據庫連接"""
        async with self.pool.acquire() as connection:
            yield connection

    async def insert_market_data(self, data: pd.DataFrame, pair_id: int):
        """批量插入市場數據"""
        async with self.acquire() as conn:
            # 準備數據
            records = [
                (
                    row['time'], pair_id, row['open'], row['high'],
                    row['low'], row['close'], row['volume'],
                    row.get('quote_volume', 0), row.get('trade_count', 0)
                )
                for _, row in data.iterrows()
            ]

            # 批量插入
            await conn.executemany(
                """
                INSERT INTO market_data
                (time, pair_id, open, high, low, close, volume, quote_volume, trade_count)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (time, pair_id) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume,
                    quote_volume = EXCLUDED.quote_volume,
                    trade_count = EXCLUDED.trade_count
                """,
                records
            )
            logger.info(f"成功插入 {len(records)} 條市場數據")

    async def get_latest_price(self, pair_id: int) -> Dict:
        """獲取最新價格"""
        async with self.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT pair_id, close as price, volume, time
                FROM market_data
                WHERE pair_id = $1
                ORDER BY time DESC
                LIMIT 1
                """,
                pair_id
            )
            return dict(row) if row else None

    async def get_ohlcv_data(
        self,
        pair_id: int,
        start_time: datetime,
        end_time: datetime,
        timeframe: str = '1m'
    ) -> pd.DataFrame:
        """獲取 OHLCV 數據"""
        # 確定時間桶大小
        timeframe_map = {
            '1m': '1 minute',
            '5m': '5 minutes',
            '15m': '15 minutes',
            '1h': '1 hour',
            '4h': '4 hours',
            '1d': '1 day'
        }
        bucket_interval = timeframe_map.get(timeframe, '1 minute')

        async with self.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    time_bucket($1::interval, time) AS time,
                    FIRST(open, time) AS open,
                    MAX(high) AS high,
                    MIN(low) AS low,
                    LAST(close, time) AS close,
                    SUM(volume) AS volume
                FROM market_data
                WHERE pair_id = $2
                    AND time >= $3
                    AND time <= $4
                GROUP BY time_bucket($1::interval, time)
                ORDER BY time
                """,
                bucket_interval, pair_id, start_time, end_time
            )

            df = pd.DataFrame(rows)
            if not df.empty:
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)
            return df

    async def get_price_statistics(
        self,
        pair_id: int,
        interval: timedelta = timedelta(days=1)
    ) -> Dict:
        """獲取價格統計信息"""
        async with self.acquire() as conn:
            row = await conn.fetchrow(
                """
                WITH price_range AS (
                    SELECT
                        MAX(high) AS high_price,
                        MIN(low) AS low_price,
                        AVG(close) AS avg_price,
                        SUM(volume) AS total_volume,
                        FIRST(open, time) AS first_open,
                        LAST(close, time) AS last_close
                    FROM market_data
                    WHERE pair_id = $1
                        AND time >= NOW() - $2::interval
                )
                SELECT
                    high_price,
                    low_price,
                    avg_price,
                    total_volume,
                    last_close - first_open AS price_change,
                    ((last_close - first_open) / first_open * 100) AS price_change_pct
                FROM price_range
                """,
                pair_id, interval
            )
            return dict(row) if row else None

    async def get_trading_pairs(self, exchange: Optional[str] = None) -> List[Dict]:
        """獲取交易對列表"""
        async with self.acquire() as conn:
            query = "SELECT * FROM trading_pairs WHERE status = 'active'"
            params = []

            if exchange:
                query += " AND exchange = $1"
                params.append(exchange)

            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    async def insert_trades(self, trades: List[Dict], pair_id: int):
        """批量插入交易記錄"""
        async with self.acquire() as conn:
            records = [
                (
                    trade['time'], trade['trade_id'], pair_id,
                    trade['price'], trade['quantity'], trade['side'],
                    trade.get('maker_order_id'), trade.get('taker_order_id')
                )
                for trade in trades
            ]

            await conn.executemany(
                """
                INSERT INTO trades
                (time, trade_id, pair_id, price, quantity, side, maker_order_id, taker_order_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (time, trade_id, pair_id) DO NOTHING
                """,
                records
            )
            logger.info(f"成功插入 {len(records)} 條交易記錄")

    async def get_volume_profile(
        self,
        pair_id: int,
        start_time: datetime,
        end_time: datetime,
        price_bins: int = 50
    ) -> pd.DataFrame:
        """獲取成交量分布"""
        async with self.acquire() as conn:
            rows = await conn.fetch(
                """
                WITH price_range AS (
                    SELECT MIN(price) AS min_price, MAX(price) AS max_price
                    FROM trades
                    WHERE pair_id = $1 AND time >= $2 AND time <= $3
                ),
                price_bins AS (
                    SELECT
                        generate_series(
                            min_price,
                            max_price,
                            (max_price - min_price) / $4
                        ) AS price_level
                    FROM price_range
                )
                SELECT
                    pb.price_level,
                    COALESCE(SUM(t.quantity), 0) AS volume,
                    COUNT(t.trade_id) AS trade_count
                FROM price_bins pb
                LEFT JOIN trades t ON
                    t.pair_id = $1
                    AND t.time >= $2
                    AND t.time <= $3
                    AND t.price >= pb.price_level
                    AND t.price < pb.price_level + (
                        SELECT (max_price - min_price) / $4 FROM price_range
                    )
                GROUP BY pb.price_level
                ORDER BY pb.price_level
                """,
                pair_id, start_time, end_time, price_bins
            )

            df = pd.DataFrame(rows)
            return df

    async def insert_orderbook_snapshot(
        self, 
        pair_id: int, 
        sequence_id: int, 
        bids: List[Tuple[float, float]], 
        asks: List[Tuple[float, float]]
    ):
        """插入訂單簿快照"""
        async with self.acquire() as conn:
            # 轉換成 JSONB 格式
            bids_json = [{"price": bid[0], "quantity": bid[1]} for bid in bids]
            asks_json = [{"price": ask[0], "quantity": ask[1]} for ask in asks]
            
            await conn.execute(
                """
                INSERT INTO orderbook_snapshots (time, pair_id, sequence_id, bids, asks)
                VALUES (NOW(), $1, $2, $3, $4)
                ON CONFLICT (time, pair_id, sequence_id) DO NOTHING
                """,
                pair_id, sequence_id, bids_json, asks_json
            )
            logger.info(f"成功插入訂單簿快照，交易對ID: {pair_id}, 序列號: {sequence_id}")

    async def insert_technical_indicator(
        self,
        pair_id: int,
        timeframe: str,
        indicator_name: str,
        indicator_value: Dict
    ):
        """插入技術指標數據"""
        async with self.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO technical_indicators 
                (time, pair_id, timeframe, indicator_name, indicator_value)
                VALUES (NOW(), $1, $2, $3, $4)
                """,
                pair_id, timeframe, indicator_name, indicator_value
            )
            logger.info(f"成功插入技術指標: {indicator_name}, 交易對ID: {pair_id}, 時間框架: {timeframe}")

    async def get_technical_indicator(
        self,
        pair_id: int,
        timeframe: str,
        indicator_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """獲取技術指標數據"""
        async with self.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT time, indicator_value
                FROM technical_indicators
                WHERE pair_id = $1
                  AND timeframe = $2
                  AND indicator_name = $3
                  AND time BETWEEN $4 AND $5
                ORDER BY time
                """,
                pair_id, timeframe, indicator_name, start_time, end_time
            )
            return [dict(row) for row in rows]


# 使用範例
async def main():
    # 初始化數據庫
    db = DataAccess("postgresql://user:password@localhost/crypto_trading")
    await db.initialize()

    try:
        # 獲取最新價格
        latest_price = await db.get_latest_price(1)
        print(f"最新價格: {latest_price}")

        # 獲取 OHLCV 數據
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        ohlcv_data = await db.get_ohlcv_data(1, start_time, end_time, '5m')
        print(f"OHLCV 數據筆數: {len(ohlcv_data)}")

        # 獲取價格統計
        stats = await db.get_price_statistics(1, timedelta(days=7))
        print(f"7日統計: {stats}")

    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())
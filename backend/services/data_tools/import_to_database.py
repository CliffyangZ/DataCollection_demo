"""
K線數據到TimescaleDB同步程式
作者: Assistant
版本: 1.0.0
描述: 從BingX交易所獲取K線數據並存儲到TimescaleDB中
"""

import json
import logging
import requests
import pandas as pd
import psycopg2
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import hashlib
import hmac
from urllib.parse import urlencode


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """載入配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self._validate_config(config)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件未找到: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式錯誤: {e}")
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """驗證配置文件格式"""
        required_keys = ['exchange_configs', 'database']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"配置文件缺少必要字段: {key}")
        
        # 驗證交易所配置
        if not config['exchange_configs']:
            raise ValueError("至少需要配置一個交易所")
        
        # 驗證數據庫配置
        db_config = config['database']
        required_db_keys = ['host', 'port', 'database', 'user', 'password']
        for key in required_db_keys:
            if key not in db_config:
                raise ValueError(f"數據庫配置缺少必要字段: {key}")
    
    def get_exchange_config(self, exchange_name: str) -> Optional[Dict[str, Any]]:
        """獲取指定交易所配置"""
        for config in self.config['exchange_configs']:
            if config['exchange_name'].lower() == exchange_name.lower():
                return config
        return None
    
    def get_database_config(self) -> Dict[str, Any]:
        """獲取數據庫配置"""
        return self.config['database']


class ErrorHandler:
    """錯誤處理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """設置日誌"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('kline_sync.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def handle_api_error(self, error: Exception, context: str) -> None:
        """處理API錯誤"""
        self.logger.error(f"API錯誤 [{context}]: {str(error)}")
    
    def handle_db_error(self, error: Exception, context: str) -> None:
        """處理數據庫錯誤"""
        self.logger.error(f"數據庫錯誤 [{context}]: {str(error)}")
    
    def handle_general_error(self, error: Exception, context: str) -> None:
        """處理一般錯誤"""
        self.logger.error(f"一般錯誤 [{context}]: {str(error)}")


class ApiClient:
    """API客戶端基類"""
    
    def __init__(self, api_config: Dict[str, Any], error_handler: ErrorHandler):
        self.api_config = api_config
        self.error_handler = error_handler
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'KlineSync/1.0.0',
            'Content-Type': 'application/json'
        })
    
    def make_request(self, endpoint: str, params: Dict[str, Any] = None, 
                    max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """發送API請求"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(endpoint, params=params, timeout=30)
                response.raise_for_status()
                
                try:
                    json_data = response.json()
                    return json_data
                except ValueError as e:
                    self.error_handler.logger.error(f"JSON解析錯誤: {str(e)}")
                    return None
                
            except requests.exceptions.RequestException as e:
                self.error_handler.handle_api_error(e, f"請求失敗 (嘗試 {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指數退避
                else:
                    return None
        return None


class BingXApiClient(ApiClient):
    """BingX API客戶端"""
    
    def __init__(self, api_config: Dict[str, Any], error_handler: ErrorHandler):
        super().__init__(api_config, error_handler) # 初始化父類
        self.base_url = api_config.get('api_url', 'https://open-api.bingx.com')
        self.api_key = api_config.get('api_key', '')
        self.secret_key = api_config.get('secret_key', '')
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """生成API簽名"""
        if not self.secret_key:
            return ''
        
        query_string = urlencode(sorted(params.items()))
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def get_kline_data(self, symbol: str, interval: str, limit: int = 500,
                      start_time: Optional[int] = None, end_time: Optional[int] = None) -> Optional[List[Union[List, Dict]]]:
        """獲取K線數據"""
        endpoint = f"{self.base_url}/openApi/swap/v3/quote/klines"
        
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': min(limit, 1000)  # BingX限制最大1000
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        # 如果有API密鑰，添加簽名
        if self.api_key:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
            self.session.headers.update({'X-BX-APIKEY': self.api_key})
        
        response = self.make_request(endpoint, params)
        if response and response.get('code') == 0:
            data = response.get('data', [])
            return data
        else:
            error_msg = response.get('msg', '未知錯誤') if response else 'API請求失敗'
            self.error_handler.handle_api_error(Exception(error_msg), f"獲取K線數據: {symbol}")
            return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """獲取交易對信息"""
        endpoint = f"{self.base_url}/openApi/swap/v2/quote/contracts"
        
        response = self.make_request(endpoint)
        if response and response.get('code') == 0:
            contracts = response.get('data', [])
            for contract in contracts:
                if contract.get('symbol') == symbol:
                    return contract
        return None


class TimescaleDBManager:
    """TimescaleDB數據庫管理器"""
    
    def __init__(self, db_config: Dict[str, Any], error_handler: ErrorHandler):
        self.db_config = db_config
        self.error_handler = error_handler
        self.connection = None
        self._connect()
        self._create_tables()
    
    def _connect(self) -> None:
        """連接數據庫"""
        try:
            self.connection = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            self.connection.autocommit = True
            self.error_handler.logger.info("數據庫連接成功")
        except psycopg2.Error as e:
            self.error_handler.handle_db_error(e, "數據庫連接")
            raise
    
    def _create_tables(self) -> None:
        """創建數據表"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS kline_data (
            time TIMESTAMPTZ NOT NULL,
            symbol VARCHAR(50) NOT NULL,
            interval VARCHAR(10) NOT NULL,
            open_price DECIMAL(20, 8) NOT NULL,
            high_price DECIMAL(20, 8) NOT NULL,
            low_price DECIMAL(20, 8) NOT NULL,
            close_price DECIMAL(20, 8) NOT NULL,
            volume DECIMAL(20, 8) NOT NULL,
            quote_volume DECIMAL(20, 8),
            trade_count INTEGER,
            taker_buy_volume DECIMAL(20, 8),
            taker_buy_quote_volume DECIMAL(20, 8),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(time, symbol, interval)
        );
        
        -- 創建超表（如果TimescaleDB可用）
        SELECT create_hypertable('kline_data', 'time', if_not_exists => TRUE);
        
        -- 創建索引
        CREATE INDEX IF NOT EXISTS idx_kline_symbol_time ON kline_data (symbol, time DESC);
        CREATE INDEX IF NOT EXISTS idx_kline_interval ON kline_data (interval, time DESC);
        CREATE INDEX IF NOT EXISTS idx_kline_symbol_interval_time ON kline_data (symbol, interval, time DESC);
        """
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(create_table_sql)
            self.error_handler.logger.info("數據表創建/檢查完成")
        except psycopg2.Error as e:
            self.error_handler.handle_db_error(e, "創建數據表")
    
    def insert_kline_data(self, df: pd.DataFrame) -> bool:
        """插入K線數據"""
        if df.empty:
            return True
        
        insert_sql = """
        INSERT INTO kline_data (
            time, symbol, interval, open_price, high_price, low_price, 
            close_price, volume, quote_volume, trade_count, 
            taker_buy_volume, taker_buy_quote_volume
        ) VALUES %s
        ON CONFLICT (time, symbol, interval) 
        DO UPDATE SET
            open_price = EXCLUDED.open_price,
            high_price = EXCLUDED.high_price,
            low_price = EXCLUDED.low_price,
            close_price = EXCLUDED.close_price,
            volume = EXCLUDED.volume,
            quote_volume = EXCLUDED.quote_volume,
            trade_count = EXCLUDED.trade_count,
            taker_buy_volume = EXCLUDED.taker_buy_volume,
            taker_buy_quote_volume = EXCLUDED.taker_buy_quote_volume
        """
        
        try:
            from psycopg2.extras import execute_values
            
            # 準備數據
            values = []
            for _, row in df.iterrows():
                values.append((
                    row['datetime'],
                    row['symbol'],
                    row['interval'],
                    float(row['open']),
                    float(row['high']),
                    float(row['low']),
                    float(row['close']),
                    float(row['volume']),
                    float(row.get('quote_volume', 0)),
                    int(row.get('trade_count', 0)),
                    float(row.get('taker_buy_volume', 0)),
                    float(row.get('taker_buy_quote_volume', 0))
                ))
            
            with self.connection.cursor() as cursor:
                execute_values(cursor, insert_sql, values, template=None, page_size=1000)
            
            self.error_handler.logger.info(f"成功插入 {len(df)} 條K線數據")
            return True
            
        except psycopg2.Error as e:
            self.error_handler.handle_db_error(e, "插入K線數據")
            return False
    
    def get_latest_timestamp(self, symbol: str, interval: str) -> Optional[datetime]:
        """獲取最新數據時間戳"""
        query_sql = """
        SELECT MAX(time) as latest_time 
        FROM kline_data 
        WHERE symbol = %s AND interval = %s
        """
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query_sql, (symbol, interval))
                result = cursor.fetchone()
                return result[0] if result and result[0] else None
        except psycopg2.Error as e:
            self.error_handler.handle_db_error(e, "查詢最新時間戳")
            return None
    
    def close(self) -> None:
        """關閉數據庫連接"""
        if self.connection:
            self.connection.close()
            self.error_handler.logger.info("數據庫連接已關閉")


class KlineDataPipeline:
    """K線數據管道"""
    
    def __init__(self, config_path: str):
        """Initialize the K-line data pipeline"""
        self.error_handler = ErrorHandler()
        self.config_manager = ConfigManager(config_path)
        
        # 初始化API客戶端
        self.api_client = self._create_api_client()
        
        # 初始化數據庫管理器
        db_config = self.config_manager.get_database_config()
        self.db_manager = TimescaleDBManager(db_config, self.error_handler)
        
        self.error_handler.logger.info("K線數據管道初始化完成")
    
    def _create_api_client(self):
        """Create the appropriate API client based on the exchange configuration"""
        # 獲取第一個交易所配置
        exchange_configs = self.config_manager.config.get('exchange_configs', [])
        if not exchange_configs:
            raise ValueError("配置文件中沒有交易所配置")
        
        exchange_config = exchange_configs[0]
        exchange_name = exchange_config.get('exchange_name', '').lower()
        api_info = exchange_config.get('api_info', {})
        
        self.error_handler.logger.info(f"使用 {exchange_name} 交易所API")
        
        # 根據交易所名稱創建相應的API客戶端
        if exchange_name == 'bingx':
            return BingXApiClient(api_info, self.error_handler)
        elif exchange_name == 'binance':
            return BinanceApiClient(api_info, self.error_handler)
        elif exchange_name == 'okx':
            return OKXApiClient(api_info, self.error_handler)
        elif exchange_name == 'bybit':
            return ByBitApiClient(api_info, self.error_handler)
        else:
            raise ValueError(f"不支持的交易所: {exchange_name}")
    
    def get_exchange_name(self) -> str:
        """Get the name of the exchange being used"""
        exchange_configs = self.config_manager.config.get('exchange_configs', [])
        if exchange_configs:
            return exchange_configs[0].get('exchange_name', 'Unknown')
        return 'Unknown'
    

    def _parse_kline_data(self, raw_data: List[Union[List, Dict]], symbol: str, interval: str) -> pd.DataFrame:
        """解析K線數據"""
        if not raw_data:
            return pd.DataFrame()
        
        try:
            # 檢查數據格式 - 處理字典格式的數據
            if isinstance(raw_data[0], dict):
                # 創建DataFrame
                df = pd.DataFrame(raw_data)
                
                # 重命名列以匹配預期格式
                rename_map = {
                    'time': 'timestamp',
                    'open': 'open',
                    'high': 'high',
                    'low': 'low',
                    'close': 'close',
                    'volume': 'volume'
                }
                
                # 僅重命名存在的列
                existing_columns = {col: rename_map[col] for col in rename_map if col in df.columns}
                df = df.rename(columns=existing_columns)
                
                # 確保所有必要的列都存在
                required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    self.error_handler.logger.warning(f"缺少必要列: {missing_columns}")
                    for col in missing_columns:
                        df[col] = None
                
                # 添加可能缺少的其他列
                optional_columns = ['quote_volume', 'trade_count', 'taker_buy_volume', 'taker_buy_quote_volume']
                for col in optional_columns:
                    if col not in df.columns:
                        df[col] = None
            else:
                # 原始格式: 列表格式 [timestamp, open, high, low, close, volume, ...]
                df = pd.DataFrame(raw_data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'quote_volume', 'trade_count', 'taker_buy_volume', 'taker_buy_quote_volume'
                ])
            
            # 數據類型轉換
            df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # 添加元數據
            df['symbol'] = symbol
            df['interval'] = interval
            
            # 數值列轉換
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 
                             'quote_volume', 'taker_buy_volume', 'taker_buy_quote_volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 確保trade_count列存在並轉換為整數
            if 'trade_count' in df.columns:
                df['trade_count'] = pd.to_numeric(df['trade_count'], errors='coerce').fillna(0).astype(int)
            
            # 數據驗證
            df = self._validate_kline_data(df)
            
            return df.sort_values('datetime')
            
        except Exception as e:
            self.error_handler.handle_general_error(e, f"解析K線數據: {symbol}")
            return pd.DataFrame()
    
    def _validate_kline_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """驗證K線數據"""
        if df.empty:
            return df
        
        # 移除無效數據
        original_count = len(df)
        
        # 移除無效時間戳
        valid_time_df = df[~pd.isna(df['datetime'])]
        df = valid_time_df
        
        # 檢查價格數據
        if not df.empty:
            # 價格必須大於0
            df = df[df['open'] > 0]
            df = df[df['high'] > 0]
            df = df[df['low'] > 0]
            df = df[df['close'] > 0]
            
            # 成交量必須大於等於0
            df = df[df['volume'] >= 0]
            
            # 去除重複時間戳
            df = df.drop_duplicates(subset=['datetime'], keep='last')
            
            # OHLC邏輯驗證
            df = df[(df['high'] >= df['open']) & 
                   (df['high'] >= df['close']) & 
                   (df['low'] <= df['open']) & 
                   (df['low'] <= df['close'])]
        
        # 記錄過濾後數據數量
        if len(df) < original_count:
            self.error_handler.logger.warning(f"數據驗證: 原始 {original_count} 條，過濾後 {len(df)} 條")
        
        return df
    
    def fetch_kline_data(self, symbol: str, interval: str = '1h', 
                        limit: int = 500, start_time: Optional[Any] = None,
                        end_time: Optional[Any] = None) -> pd.DataFrame:
        """獲取K線數據"""
        self.error_handler.logger.info(f"開始獲取K線數據: {symbol} {interval}")
        
        # 轉換datetime對象為毫秒時間戳
        if start_time is not None and isinstance(start_time, datetime):
            start_time = int(start_time.timestamp() * 1000)
        
        if end_time is not None and isinstance(end_time, datetime):
            end_time = int(end_time.timestamp() * 1000)
        
        raw_data = self.api_client.get_kline_data(
            symbol=symbol,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time
        )
        
        if raw_data is None:
            self.error_handler.logger.error(f"獲取K線數據失敗: {symbol}")
            return pd.DataFrame()
        
        df = self._parse_kline_data(raw_data, symbol, interval)
        self.error_handler.logger.info(f"成功獲取 {len(df)} 條K線數據: {symbol}")
        
        return df
    
    def sync_kline_data(self, symbol: str, interval: str = '1h', 
                       limit: int = 500, incremental: bool = True) -> bool:
        """同步K線數據到數據庫"""
        try:
            start_time = None
            
            # 增量同步：獲取最新時間戳
            if incremental:
                latest_time = self.db_manager.get_latest_timestamp(symbol, interval)
                if latest_time:
                    # 從最新時間戳之後開始獲取
                    start_time = int(latest_time.timestamp() * 1000) + 1
                    self.error_handler.logger.info(f"增量同步從 {latest_time} 開始")
            
            # 獲取數據
            df = self.fetch_kline_data(
                symbol=symbol,
                interval=interval,
                limit=limit,
                start_time=start_time
            )
            
            if df.empty:
                self.error_handler.logger.info(f"沒有新數據需要同步: {symbol}")
                return True
            
            # 存儲到數據庫
            success = self.db_manager.insert_kline_data(df)
            
            if success:
                self.error_handler.logger.info(
                    f"成功同步K線數據: {symbol} {interval} ({len(df)} 條)"
                )
            
            return success
            
        except Exception as e:
            self.error_handler.handle_general_error(e, f"同步K線數據: {symbol}")
            return False
    
    def sync_multiple_symbols(self, symbols: List[str], interval: str = '1h',
                            limit: int = 500, delay: float = 1.0) -> Dict[str, bool]:
        """批量同步多個交易對"""
        results = {}
        
        self.error_handler.logger.info(f"開始批量同步 {len(symbols)} 個交易對")
        
        for i, symbol in enumerate(symbols):
            self.error_handler.logger.info(f"同步進度: {i+1}/{len(symbols)} - {symbol}")
            
            success = self.sync_kline_data(symbol, interval, limit)
            results[symbol] = success
            
            # 添加延遲避免API限制
            if i < len(symbols) - 1:
                time.sleep(delay)
        
        # 統計結果
        success_count = sum(1 for success in results.values() if success)
        self.error_handler.logger.info(
            f"批量同步完成: 成功 {success_count}/{len(symbols)}"
        )
        
        return results
    
    def get_symbol_list(self) -> List[str]:
        """獲取可用交易對列表"""
        try:
            endpoint = f"{self.api_client.base_url}/openApi/swap/v2/quote/contracts"
            
            response = self.api_client.make_request(endpoint)
            
            if response and response.get('code') == 0:
                contracts = response.get('data', [])
                symbols = [contract['symbol'] for contract in contracts if contract.get('symbol')]
                self.error_handler.logger.info(f"獲取到 {len(symbols)} 個交易對")
                return symbols
            else:
                self.error_handler.logger.error("獲取交易對列表失敗")
                return []
                
        except Exception as e:
            self.error_handler.handle_general_error(e, "獲取交易對列表")
            return []
    
    def close(self) -> None:
        """關閉所有連接"""
        if hasattr(self, 'db_manager'):
            self.db_manager.close()
        if hasattr(self, 'api_client') and hasattr(self.api_client, 'session'):
            self.api_client.session.close()
        self.error_handler.logger.info("K線數據管道已關閉")


def main():
    """主函數 - 示例用法"""
    try:
        # 初始化管道
        pipeline = KlineDataPipeline('config.json')
        
        # 示例1: 同步單個交易對
        print("=== 同步BTC-USDT 1小時K線數據 ===")
        success = pipeline.sync_kline_data('BTC-USDT', interval='1h', limit=100)
        print(f"同步結果: {'成功' if success else '失敗'}")
        
        # 示例2: 批量同步
        print("\\n=== 批量同步多個交易對 ===")
        symbols = ['BTC-USDT', 'ETH-USDT', 'BNB-USDT']
        results = pipeline.sync_multiple_symbols(symbols, interval='1d', limit=30)
        
        print("批量同步結果:")
        for symbol, success in results.items():
            print(f"  {symbol}: {'成功' if success else '失敗'}")
        
    except Exception as e:
        print(f"程式執行錯誤: {e}")
    finally:
        if 'pipeline' in locals():
            pipeline.close()

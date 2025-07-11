#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
K線數據持續收集腳本
用於從交易所API收集指定交易對的K線數據並存入數據庫
支持指定時間範圍和交易對

使用方法:
python backend/scripts/data/keep_collecting.py --symbol BTC-USDT --start_time 2025-01-01 --end_time 2025-07-02 --interval 1h --config_path /Users/cliffyang/Documents/Program/Crypto_Trading_Bot/TradingModel_V3/backend/api_config/BingX_api_config2_local.json
"""

import sys
import os
import argparse
import logging
from datetime import datetime, timedelta
import time
import pandas as pd

# 添加項目根目錄到系統路徑，以便正確導入模塊
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.insert(0, project_root)

# 直接導入模塊，不使用backend前綴
from backend.services.data_tools.import_to_database import KlineDataPipeline, ErrorHandler

def setup_logger():
    """設置日誌記錄器"""
    logger = logging.getLogger('data_collector')
    logger.setLevel(logging.INFO)
    
    # 創建控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 創建文件處理器
    file_handler = logging.FileHandler('data_collection.log')
    file_handler.setLevel(logging.INFO)
    
    # 創建格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 添加處理器到日誌記錄器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def parse_arguments():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description='從交易所API收集K線數據')
    
    parser.add_argument('--symbol', type=str, required=True, help='交易對，例如 BTC-USDT')
    parser.add_argument('--start_time', type=str, required=True, help='開始時間，格式 YYYY-MM-DD')
    parser.add_argument('--end_time', type=str, required=False, help='結束時間，格式 YYYY-MM-DD，默認為當前時間')
    parser.add_argument('--interval', type=str, default='1h', help='K線間隔，例如 1m, 5m, 15m, 30m, 1h, 4h, 1d')
    parser.add_argument('--batch_size', type=int, default=1000, help='每批次請求的K線數量，最大1000')
    parser.add_argument('--config_path', type=str, required=True, help='配置文件路徑')
    parser.add_argument('--sleep_time', type=int, default=1, help='每批次請求之間的休眠時間（秒）')
    
    return parser.parse_args()

def str_to_timestamp(date_str):
    """將日期字符串轉換為毫秒時間戳"""
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    return int(dt.timestamp() * 1000)

def timestamp_to_str(timestamp_ms):
    """將毫秒時間戳轉換為日期字符串"""
    dt = datetime.fromtimestamp(timestamp_ms / 1000)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def collect_kline_data(args, logger):
    """收集K線數據的主函數"""
    try:
        # 初始化數據管道
        pipeline = KlineDataPipeline(args.config_path)
        exchange_name = pipeline.get_exchange_name()
        logger.info(f"使用配置文件: {args.config_path}")
        logger.info(f"使用交易所: {exchange_name}")
        
        # 解析時間範圍
        start_timestamp = str_to_timestamp(args.start_time)
        
        if args.end_time:
            end_timestamp = str_to_timestamp(args.end_time)
            # 設置為當天的23:59:59
            end_timestamp += 86399000  # 23小時59分59秒的毫秒數
        else:
            end_timestamp = int(datetime.now().timestamp() * 1000)
        
        logger.info(f"開始收集 {args.symbol} 的 {args.interval} K線數據")
        logger.info(f"時間範圍: {timestamp_to_str(start_timestamp)} 至 {timestamp_to_str(end_timestamp)}")
        
        # 計算總時間範圍
        total_time_range = end_timestamp - start_timestamp
        
        # 估算K線數量（粗略計算）
        interval_ms = {
            '1m': 60 * 1000,
            '5m': 5 * 60 * 1000,
            '15m': 15 * 60 * 1000,
            '30m': 30 * 60 * 1000,
            '1h': 60 * 60 * 1000,
            '4h': 4 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000
        }
        
        estimated_klines = total_time_range / interval_ms.get(args.interval, 3600000)
        logger.info(f"預計需要收集約 {int(estimated_klines)} 條K線數據")
        
        # 分批收集數據
        current_start = start_timestamp
        total_collected = 0
        batch_count = 0
        
        while current_start < end_timestamp:
            batch_count += 1
            current_end = min(current_start + (args.batch_size * interval_ms.get(args.interval, 3600000)), end_timestamp)
            
            logger.info(f"收集批次 {batch_count}: {timestamp_to_str(current_start)} 至 {timestamp_to_str(current_end)}")
            
            # 獲取K線數據
            df = pipeline.fetch_kline_data(
                symbol=args.symbol,
                interval=args.interval,
                limit=args.batch_size,
                start_time=current_start,
                end_time=current_end
            )
            
            # 插入數據庫
            if not df.empty:
                success = pipeline.db_manager.insert_kline_data(df)
                if success:
                    logger.info(f"成功插入 {len(df)} 條K線數據")
                    total_collected += len(df)
                else:
                    logger.error("數據庫插入失敗")
            else:
                logger.warning(f"該時間段沒有獲取到有效數據: {timestamp_to_str(current_start)} 至 {timestamp_to_str(current_end)}")
            
            # 更新下一批次的開始時間
            if len(df) > 0:
                # 使用最後一條數據的時間戳作為下一批次的開始時間
                last_timestamp = df['timestamp'].max()
                current_start = last_timestamp + interval_ms.get(args.interval, 3600000)
            else:
                # 如果沒有數據，則按照批次大小向前移動
                current_start = current_end
            
            # 休眠一段時間，避免API請求過於頻繁
            logger.info(f"休眠 {args.sleep_time} 秒...")
            time.sleep(args.sleep_time)
            
            # 顯示進度
            progress = min(100, (current_start - start_timestamp) / total_time_range * 100)
            logger.info(f"總進度: {progress:.2f}% 已收集: {total_collected} 條")
        
        logger.info(f"數據收集完成! 總共收集了 {total_collected} 條 {args.symbol} 的 {args.interval} K線數據")
        return True
        
    except Exception as e:
        logger.error(f"數據收集過程中發生錯誤: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主函數"""
    args = parse_arguments()
    logger = setup_logger()
    
    logger.info("開始執行數據收集腳本")
    logger.info(f"參數信息: symbol={args.symbol}, 開始時間={args.start_time}, 結束時間={args.end_time}")
    logger.info(f"配置文件路徑: {args.config_path}")
    logger.info(f"配置文件是否存在: {os.path.exists(args.config_path)}")
    
    try:
        # 修正路徑問題，確保使用絕對路徑
        if not os.path.exists(args.config_path) and '/backend/api_config/' in args.config_path:
            # 嘗試修正路徑
            original_path = args.config_path
            corrected_path = os.path.join(project_root, 'backend', 'api_config', os.path.basename(args.config_path))
            logger.info(f"嘗試使用修正後的路徑: {corrected_path}")
            args.config_path = corrected_path
            logger.info(f"修正後的配置文件是否存在: {os.path.exists(args.config_path)}")
            
        success = collect_kline_data(args, logger)
        logger.info("數據收集完成")
    except FileNotFoundError as e:
        logger.error(f"配置文件未找到: {str(e)}")
        logger.error(f"完整路徑: {os.path.abspath(args.config_path)}")
        logger.error(f"項目根目錄: {project_root}")
        logger.error(f"目錄內容: {os.listdir(os.path.dirname(args.config_path) if os.path.exists(os.path.dirname(args.config_path)) else project_root)}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"參數錯誤: {str(e)}")
        sys.exit(1)
    except psycopg2.OperationalError as e:
        logger.error(f"數據庫連線錯誤: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"數據收集失敗: {str(e)}")
        import traceback
        logger.error(f"詳細錯誤信息: {traceback.format_exc()}")
        sys.exit(1)
    
    if success:
        logger.info("腳本執行成功")
        return 0
    else:
        logger.error("腳本執行失敗")
        return 1

if __name__ == "__main__":
    sys.exit(main())
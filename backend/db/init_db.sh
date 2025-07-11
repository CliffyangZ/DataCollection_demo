#!/bin/bash

set -e

echo "正在初始化加密貨幣交易數據庫..."

# 連接到數據庫
export PGPASSWORD=kevin0130
PSQL="psql -h localhost -U postgres -d crypto_data"

# 執行遷移腳本
echo "正在應用數據庫結構..."
$PSQL -f migrations/01_initial_schema.sql

echo "正在應用優化配置..."
$PSQL -f migrations/02_optimization.sql

# 可選: 如果需要填充測試數據
if [ "$1" = "--with-test-data" ]; then
  echo "正在填充測試數據..."
  $PSQL -f migrations/03_testing.sql
fi

echo "數據庫初始化完成!"
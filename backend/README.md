# TradingBot_V3 Backend

本目錄為 TradingBot_V3 的後端服務，負責數據收集、API 提供、數據庫管理等核心功能。

## 目錄結構與組件說明

- **api/**
  - 提供 FastAPI 應用與 RESTful API 端點。
  - 集中管理與前端的 HTTP 交互。
- **api_config/**
  - 儲存各交易所的 API 配置檔（如 Binance、OKX、BingX 等 JSON 檔）。
- **db/**
  - 數據庫連接與管理相關腳本，例如資料庫 session、遷移腳本等。
- **logs/**
  - 儲存後端各模組運行產生的日誌文件。
- **main_function/**
  - 主要數據同步與處理流程腳本。
- **scripts/**
  - 輔助腳本，如批次任務、工具腳本等。
- **services/**
  - 業務邏輯與數據處理模組，包含資料獲取、清洗、同步等。
- **settings/**
  - 配置管理與環境變數相關設定。
- **requirements.txt**
  - Python 依賴包清單。
- **.env**
  - 環境變數配置（如資料庫連線、API 金鑰等）。

## 主要功能

1. **多交易所數據收集**：
   - 從多個主流交易所（Binance、OKX、BingX、Bybit 等）自動收集 K 線數據。
   - 支持定時與手動同步。
2. **RESTful API 提供**：
   - 使用 FastAPI 提供數據查詢、狀態查詢等 API。
   - 支援與前端 Vue.js 應用互動。
3. **數據庫管理與同步**：
   - 支持 TimescaleDB/PostgreSQL 作為主要資料庫。
   - 數據同步、批量導入與查詢。
4. **日誌與監控**：
   - 完整日誌記錄，便於追蹤數據同步與錯誤。
   - 可擴展 Prometheus 監控。
5. **Docker 支援**：
   - 可通過 Docker 容器化部署。

## 啟動方式（開發環境）

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn api.app:app --reload --host 0.0.0.0 --port 5000
```

## 聯絡與貢獻
如需協助或想參與開發，請提交 Issue 或 Pull Request。

# TradingBot_V3- 數據收集可視化介面

## 項目概述
這個項目為加密貨幣交易系統的數據收集過程提供了一個可視化介面，使用Vue.js實現前端，Flask實現後端API。通過這個介面，您可以：

1. 啟動和監控數據收集任務
2. 實時查看收集進度和統計數據
3. 可視化展示收集歷史和速率

## 系統架構
- **前端**: Vue.js 3 + Vuetify 3 + Chart.js
- **後端API**: Flask + Flask-CORS
- **數據庫**: PostgreSQL with TimescaleDB
- **容器化**: Docker + Docker Compose

## 目錄結構
```
TradingBot_V3/
├── backend/
│   ├── api/              # 後端API服務
│   │   ├── app.py        # Flask應用
│   │   ├── Dockerfile    # 後端Docker配置
│   │   └── requirements.txt
│   ├── scripts/          # 數據收集腳本
│   └── services/         # 後端服務
├── frontend/             # Vue.js前端
│   ├── src/              # 源代碼
│   ├── Dockerfile        # 前端Docker配置
│   └── nginx.conf        # Nginx配置
└── docker-compose.yml    # Docker Compose配置
```

## 安裝與運行

###設定config.json和環境變數
1. backend 需要設定api_config及.env的database setting
2. 設定docker-compose.yml database設定，volumn設定

### 使用Docker Compose（推薦）
1. 確保已安裝Docker和Docker Compose
2. 在項目根目錄執行：
```bash
docker-compose up -d
```
3. 訪問 http://localhost:3000 查看前端界面
4. API服務運行在 http://localhost:5000

### 手動運行
#### 前端
```bash
cd frontend
npm install
npm run dev
```

#### 後端API
```bash
cd backend/api
pip install -r requirements.txt
python app.py
```

## 使用指南

### 數據收集控制面板
1. 填寫交易對、時間間隔、開始時間等參數
2. 點擊「開始收集」按鈕啟動收集任務
3. 可以隨時點擊「停止收集」按鈕中斷任務

### 收集進度監控
- 實時顯示收集進度條和百分比
- 顯示已收集的K線數量和總批次數
- 計算並顯示收集速率和預計剩餘時間

### 收集歷史圖表
- 顯示每批次收集的數據量
- 顯示總體收集進度變化
- 可以點擊刷新按鈕更新圖表

## 開發說明

### 前端開發
前端使用Vue.js 3和Composition API開發，主要組件包括：
- `DataCollectionView.vue`: 主視圖組件
- `CollectionHistoryChart.vue`: 收集歷史圖表組件
- `dataCollectionStore.js`: Pinia狀態管理

### 後端開發
後端使用Flask開發RESTful API，主要功能包括：
- 啟動/停止數據收集任務
- 監控收集進度並提供實時狀態
- 解析日誌文件獲取詳細信息

## 注意事項
- 確保配置文件路徑正確
- 數據庫連接需要正確配置
- 大量數據收集可能需要較長時間，請耐心等待
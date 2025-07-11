# TradingBot_V3 - 前端

## 技術棧
- Vue.js 3
- Vite
- Pinia (狀態管理)
- Vue Router (路由管理)
- Material Design 3 (UI 設計系統)
- Chart.js/Lightweight Charts (圖表庫)
- Socket.io-client (實時通訊)

## 目錄結構
```
frontend/
├── public/              # 靜態資源
├── src/                 # 源代碼
│   ├── assets/          # 資源文件
│   ├── components/      # 共用組件
│   ├── layouts/         # 布局組件
│   ├── router/          # 路由配置
│   ├── stores/          # Pinia 狀態管理
│   ├── services/        # API 服務
│   ├── utils/           # 工具函數
│   ├── views/           # 頁面視圖
│   ├── App.vue          # 根組件
│   └── main.js          # 入口文件
├── .env                 # 環境變數
├── index.html           # HTML 模板
├── package.json         # 依賴配置
└── vite.config.js       # Vite 配置
```

### 主要目錄
assets/：靜態資源文件
圖片、字體、樣式等
components/：可重用的 Vue 組件
例如：按鈕、表單、卡片等通用組件
views/：頁面級組件
DataCollectionView.vue：數據收集頁面
KlineChartView.vue：K線圖表展示頁面
stores/：Pinia 狀態管理
管理應用的全局狀態
例如：用戶認證、數據緩存等
services/：API 服務
封裝與後端 API 的通信邏輯
例如：api.js 封裝 HTTP 請求
router/：路由配置


## 安裝與運行

### 安裝依賴
```bash
cd frontend
npm install
```

### 開發模式運行
```bash
npm run dev
```

### 構建生產版本
```bash
npm run build
```

## 主要功能模塊

### 1. 用戶認證模塊
- 登錄/註冊頁面
- JWT 認證存儲
- 用戶資料頁面

### 2. 交易視圖模塊
- K線圖表
- 交易訂單面板
- 持倉管理

### 3. 市場數據模塊
- 市場行情列表
- 深度圖表
- 實時數據更新

### 4. 交易記錄模塊
- 訂單歷史
- 交易記錄
- 收益分析

## 狀態管理設計
使用 Pinia 管理以下狀態:
- 用戶認證狀態
- 市場數據狀態
- 交易狀態
- 持倉狀態
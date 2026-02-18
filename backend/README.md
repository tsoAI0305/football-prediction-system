# 足球賽事預測分析系統 - 後端 API

AI-powered football match prediction system with ML analysis and betting insights

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

## 🎯 專案簡介

這是一個基於 AI 的足球賽事預測系統後端，整合了機器學習模型和 LLM 分析，為足球賽事提供：

- 🤖 **AI 預測分析** - 使用 XGBoost/LightGBM 預測比賽結果
- 📊 **數據驅動決策** - 基於歷史數據和即時賠率分析
- 💡 **投注建議** - 提供價值投注推薦和信心指數
- 🧠 **LLM 深度分析** - 整合大語言模型進行新聞和情緒分析
- 📈 **歷史追蹤** - 記錄預測準確率並持續優化

## 🚀 快速開始

### 前置需求

- Docker & Docker Compose
- Python 3.11+ (本地開發時)

### 一鍵啟動

```bash
# 1. 克隆專案
git clone https://github.com/tsoAI0305/football-prediction-system.git
cd football-prediction-system/backend

# 2. 設定環境變數
cp .env.example .env
# 編輯 .env 填入你的配置（可選，使用預設值也能運行）

# 3. 啟動所有服務 (PostgreSQL + Redis + API)
docker-compose up -d

# 4. 查看服務狀態
docker-compose ps

# 5. 訪問 API 文檔
# 瀏覽器打開: http://localhost:8000/docs
```

### 驗證安裝

```bash
# 檢查健康狀態
curl http://localhost:8000/health

# 預期輸出
{
  "status": "healthy",
  "database": "healthy",
  "redis": "healthy"
}
```

## 📊 API 端點

### 健康檢查

```http
GET /health
```

返回 API、資料庫和 Redis 的健康狀態。

### 賽事列表

```http
GET /api/matches?league=ENG_PL&date=2026-02-18&limit=20
```

**查詢參數：**
- `league` - 聯賽篩選 (如: ENG_PL, GER_B1, ESP_L1)
- `date` - 日期篩選 (格式: YYYY-MM-DD)
- `status` - 狀態篩選 (scheduled, live, finished, postponed)
- `limit` - 返回數量 (預設20，最多100)

**範例回應：**
```json
{
  "total": 5,
  "matches": [
    {
      "id": 1,
      "league": "ENG_PL",
      "match_date": "2026-02-18T15:00:00",
      "status": "scheduled",
      "home_team": {
        "id": 1,
        "name": "Manchester United",
        "current_points": 45,
        "current_rank": 3
      },
      "away_team": {
        "id": 2,
        "name": "Liverpool",
        "current_points": 50,
        "current_rank": 2
      },
      "odds": {
        "home": 2.5,
        "draw": 3.2,
        "away": 2.8
      }
    }
  ]
}
```

### 單場比賽詳情

```http
GET /api/matches/{match_id}
```

獲取比賽的詳細資訊，包含球隊統計和預測記錄。

### AI 預測分析

```http
GET /api/predictions/{match_id}
```

獲取或生成比賽的 AI 預測分析。

**範例回應：**
```json
{
  "id": 1,
  "match_id": 1,
  "prediction": {
    "result": "H",
    "probabilities": {
      "home": 0.55,
      "draw": 0.25,
      "away": 0.20
    },
    "ai_score": 7.8
  },
  "betting": {
    "advice": "建議小注主勝（信心度: 55.0%）",
    "value_rating": 6.5
  },
  "analysis": {
    "llm_analysis": "【AI 深度分析】\n\n本場比賽 Manchester United 主場迎戰 Liverpool...",
    "news_sentiment": 0.3
  },
  "created_at": "2026-02-18T10:00:00"
}
```

### 歷史預測記錄

```http
GET /api/history?limit=30&only_completed=false
```

**查詢參數：**
- `limit` - 返回數量 (預設30，最多100)
- `only_completed` - 是否只顯示已完賽的預測

**範例回應：**
```json
{
  "total": 15,
  "correct": 10,
  "accuracy": 66.67,
  "predictions": [...]
}
```

## 🛠️ 技術棧

### 核心框架
- **FastAPI** 0.104+ - 現代 Python Web 框架
- **Uvicorn** - ASGI 伺服器
- **Pydantic** - 資料驗證

### 資料庫
- **PostgreSQL** 15 - 主資料庫
- **SQLAlchemy** 2.0 - ORM
- **Alembic** - 資料庫遷移

### 快取 & 任務
- **Redis** 7 - 快取和消息佇列
- **Celery** - 非同步任務排程

### 機器學習
- **scikit-learn** - ML 基礎庫
- **XGBoost** - 梯度提升模型
- **LightGBM** - 輕量級梯度提升
- **pandas** & **numpy** - 數據處理

### LLM 整合
- **LangChain** - LLM 應用框架
- **OpenAI API** - 支援自定義 base_url (相容 Groq)

### 其他工具
- **BeautifulSoup4** - 網頁爬蟲
- **pytest** - 單元測試
- **Docker** - 容器化部署

## 📁 專案結構

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 主應用程式
│   ├── config.py               # 配置管理
│   ├── database.py             # 資料庫連接
│   │
│   ├── models/                 # SQLAlchemy ORM 模型
│   │   ├── __init__.py
│   │   ├── match.py           # 比賽資料模型
│   │   ├── prediction.py      # 預測記錄模型
│   │   └── team.py            # 球隊資料模型
│   │
│   ├── schemas/                # Pydantic 資料驗證
│   │   ├── __init__.py
│   │   ├── match.py
│   │   ├── prediction.py
│   │   └── response.py
│   │
│   ├── routers/                # API 路由
│   │   ├── __init__.py
│   │   ├── health.py          # 健康檢查
│   │   ├── matches.py         # 賽事 API
│   │   ├── predictions.py     # 預測 API
│   │   └── history.py         # 歷史記錄
│   │
│   ├── services/               # 業務邏輯層
│   │   ├── __init__.py
│   │   ├── ml_service.py      # ML 模型服務
│   │   └── llm_service.py     # LLM 分析服務
│   │
│   ├── scrapers/               # 數據爬蟲 (待實作)
│   ├── ml/                     # 機器學習模組 (待實作)
│   ├── tasks/                  # Celery 任務 (待實作)
│   │
│   └── utils/                  # 工具函數
│       ├── __init__.py
│       ├── cache.py           # Redis 快取
│       └── logger.py          # 日誌配置
│
├── tests/                      # 單元測試
│   ├── __init__.py
│   └── test_api.py
│
├── data/                       # 數據存放 (gitignore)
├── models/                     # 訓練好的模型 (gitignore)
│
├── .env.example                # 環境變數範例
├── .gitignore
├── requirements.txt            # Python 依賴
├── Dockerfile                  # Docker 配置
├── docker-compose.yml          # Docker Compose
└── README.md
```

## 🔧 本地開發

### 設置開發環境

```bash
# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 啟動資料庫和 Redis (使用 Docker)
docker-compose up db redis -d

# 設定環境變數
cp .env.example .env
# 編輯 .env 設定 DATABASE_URL 和其他配置

# 初始化資料庫
python -c "from app.database import init_db; init_db()"

# 啟動開發伺服器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 執行測試

```bash
# 執行所有測試
pytest tests/ -v

# 執行特定測試
pytest tests/test_api.py::test_health_check -v

# 查看測試覆蓋率
pytest tests/ --cov=app --cov-report=html
```

### 資料庫管理

```bash
# 進入 PostgreSQL 容器
docker exec -it backend-db-1 psql -U football_user -d football_db

# 查看資料表
\dt

# 查看球隊資料
SELECT * FROM teams;

# 查看比賽資料
SELECT * FROM matches;
```

## 🌍 環境變數說明

在 `.env` 檔案中配置以下變數：

```bash
# 資料庫連接
DATABASE_URL=postgresql://football_user:football_pass@localhost:5432/football_db

# Redis 連接
REDIS_URL=redis://localhost:6379/0

# LLM 配置 (使用 Groq 免費 API)
LLM_API_KEY=your_groq_api_key_here
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.1-70b-versatile

# API 配置
DEBUG=True
SECRET_KEY=change-this-to-random-secret-key
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Celery (可選)
CELERY_BROKER_URL=redis://localhost:6379/1
```

### 獲取 Groq API Key

1. 訪問 [Groq Console](https://console.groq.com/)
2. 註冊並登入
3. 創建 API Key
4. 將 Key 填入 `.env` 的 `LLM_API_KEY`

## 🐳 Docker 部署

### 生產環境部署

```bash
# 構建映像
docker-compose build

# 啟動服務
docker-compose up -d

# 查看日誌
docker-compose logs -f api

# 停止服務
docker-compose down

# 清除所有資料 (包含資料庫)
docker-compose down -v
```

### 服務端口

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 📈 使用範例

### Python 客戶端

```python
import requests

# API 基礎 URL
BASE_URL = "http://localhost:8000"

# 獲取今天的比賽
response = requests.get(f"{BASE_URL}/api/matches", params={
    "date": "2026-02-18",
    "league": "ENG_PL"
})
matches = response.json()

# 獲取第一場比賽的預測
if matches["total"] > 0:
    match_id = matches["matches"][0]["id"]
    prediction = requests.get(f"{BASE_URL}/api/predictions/{match_id}")
    print(prediction.json())
```

### cURL 範例

```bash
# 健康檢查
curl http://localhost:8000/health

# 獲取英超賽事
curl "http://localhost:8000/api/matches?league=ENG_PL"

# 獲取預測
curl http://localhost:8000/api/predictions/1

# 獲取歷史記錄
curl "http://localhost:8000/api/history?limit=10"
```

## 🔒 安全性

- 使用環境變數管理敏感資訊
- API Key 不提交到版本控制
- PostgreSQL 密碼建議使用強密碼
- 生產環境應啟用 HTTPS
- 建議使用反向代理 (如 Nginx)

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

1. Fork 本專案
2. 創建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📝 待辦事項

- [ ] 實作完整的爬蟲模組
- [ ] 訓練和部署 ML 模型
- [ ] 整合真實的 LLM API
- [ ] 實作 Celery 定時任務
- [ ] 加入資料庫遷移 (Alembic)
- [ ] 增加更多單元測試
- [ ] 加入 CI/CD 流程
- [ ] 性能優化和快取策略
- [ ] API 限流和認證

## 📄 授權

MIT License

Copyright (c) 2026 Football Prediction System

## 📧 聯絡方式

如有問題或建議，請開 Issue 或聯繫維護者。

---

Made with ❤️ using FastAPI and Python

# ⚽ AI 足球預測系統
![GitHub stars](https://img.shields.io/github/stars/tsoAI0305/football-prediction-system?style=social)
![GitHub forks](https://img.shields.io/github/forks/tsoAI0305/football-prediction-system?style=social)
![GitHub issues](https://img.shields.io/github/issues/tsoAI0305/football-prediction-system)
![GitHub license](https://img.shields.io/github/license/tsoAI0305/football-prediction-system)
![Python version](https://img.shields.io/badge/python-3.11-blue)
![Next.js version](https://img.shields.io/badge/next.js-14-black)

> Full-Stack AI Application for Football Match Prediction

結合機器學習與大型語言模型的智能足球比賽預測平台

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

## 🎯 專案簡介

AI 足球預測系統是一個全棧 Web 應用，整合了傳統統計模型與先進的大型語言模型（Groq Llama 3.3 70B），提供五大聯賽比賽的智能預測與深度分析。

**核心價值：**
- ✅ 數據驅動的預測模型（基於歷史戰績、主客場優勢、近期狀態）
- ✅ AI 深度分析（Groq Llama 3.3 70B，100% 覆蓋率）
- ✅ 現代化用戶界面（Next.js 14 + Tailwind CSS + Framer Motion）
- ✅ Docker 一鍵部署


## 📚 文檔資源

| 資源 | 連結 | 說明 |
|------|------|------|
| 📖 README | [查看文檔](https://github.com/tsoAI0305/football-prediction-system#readme) | 完整專案說明 |
| 📊 簡報 PDF | [下載簡報](https://github.com/tsoAI0305/football-prediction-system/blob/main/docs/AI-Football-Prediction-System.pdf) | 專案技術簡報 |
| 📸 系統截圖 | [查看截圖](https://github.com/tsoAI0305/football-prediction-system/tree/main/docs/screenshots) | 8 張功能展示 |
| 📚 API 文檔 | [Swagger UI](http://localhost:8000/docs) | 互動式 API 文檔 |
| 🤝 貢獻指南 | [查看指南](https://github.com/tsoAI0305/football-prediction-system/blob/main/CONTRIBUTING.md) | 如何貢獻程式碼 |
| 🏷️ 版本發布 | [查看 Releases](https://github.com/tsoAI0305/football-prediction-system/releases) | 版本歷程 |
## ✨ 核心功能

### 🔮 比賽預測
- **47 場五大聯賽比賽**即時預測
- **多維度評分系統**（綜合實力 0-100 分）
- 預測結果：**勝率百分比** + **預測比分** + **信心度評估**

### 🤖 AI 深度分析
- **技術**：Groq Llama 3.3 70B Versatile
- **覆蓋率**：100%（47/47 場比賽）
- **分析內容**：關鍵因素分析、風險提示、AI 專業建議

### 📈 球隊詳情頁
- 主客場勝率、綜合實力排名、近期狀態、場均進球統計

### 🎨 互動式介面
- 按聯賽篩選、按結果篩選、球隊搜尋功能、流暢動畫效果

## 🛠️ 技術架構

**後端**：FastAPI + Python 3.11 + Groq API  
**前端**：Next.js 14 + TypeScript + Tailwind CSS  
**部署**：Docker + Docker Compose

## 🚀 快速開始

**安裝流程**

```bash
git clone https://github.com/tsoAI0305/football-prediction-system.git
cd football-prediction-system

# 設定環境變數
echo "GROQ_API_KEY=your_api_key_here" > backend/.env

# 啟動後端
cd backend
docker compose up -d

# 訪問前端
# 前端：http://localhost:3000
# 後端 API：http://localhost:8000/docs
```

---

## 🎯 技術亮點

1. **AI 自動分析完整流程**
   - Groq Llama 3.3 70B API 串接
   - 原始數據自動轉換 AI 賽評
2. **模組化架構設計**
   - 前後端分離，API 可擴展
   - 多賽事、多模型自動切換
3. **極速部署**
   - 完整 Docker 化
   - 支援本地＆雲端自動啟動

---

## 🏗️ 專案結構

```text
football-prediction-system/
├── backend/
│   ├── app/                    # FastAPI 應用
│   ├── scripts/                # 賽事預測腳本
│   └── data/                   # 來源數據/特徵
└── frontend/
    ├── app/                   # Next.js 主要頁面
    └── components/            # React 組件
```

---

## 📈 AI 預測說明

- **AI 分析流程：**
  - 預測輸入 ➔ Groq API ➔ Llama 3.3 70B ➔ 中文自然語言賽評
- **評分維度&權重：**
  - 歷史戰績(40%)、主客場優勢(30%)、近期狀態(20%)、進攻能力(10%)
- **預測結果   **
  - 勝率百分比、預測比分、信心度、AI 風險提示

---

## 🎨 主要功能

- 47 場五大聯賽比賽自動預測
- 多維度動態評分 (0-100 分)
- AI 智能賽評（100% coverage）
- 球隊搜尋、結果篩選、動態動畫、主客場圖表
- API 全 Swagger 文件

---

## 🔌 API 端點（範例）

- `GET /api/predictions?league=Premier%20League`  
  獲取比賽預測結果
- `GET /api/teams/Arsenal`  
  獲取指定球隊近期狀態/綜合資訊  
- 完整說明見 [Swagger UI](http://localhost:8000/docs)

---

## 🔮 未來規劃

- 自動爬蟲/批次更新賽程
- 歷史預測準確度追蹤 &排名
- 用戶註冊/收藏對戰
- 多語言切換

---

## 📊 專案統計

- 📄 6071 行程式碼
- 🏟️ 47 場比賽 AI 預測
- 💯 分析覆蓋率 100%
- 🗂️ 53 個檔案、完整雙端 Docker 工作流

---

## 📜 授權
MIT License

---

## 👤 作者
- tsoAI0305  
  - GitHub: [@tsoAI0305](https://github.com/tsoAI0305)
  - Portfolio: [作品集](https://github.com/tsoAI0305/portfolio)

---

## 🙏 致謝
- Groq - AI 引擎
- FastAPI/Next.js - 官方開源框架
- 所有社群數據夥伴

---

## 🔗 更多專案

查看完整作品集：[**tsoAI0305 Portfolio**](https://github.com/tsoAI0305/portfolio)

---

⭐ 如果這個專案對你有幫助，請給個 Star！

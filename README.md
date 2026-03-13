# ⚽ AI 足球預測系統
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

### 安裝步驟

1. 克隆倉庫
```bash
git clone https://github.com/tsoAI0305/football-prediction-system.git
cd football-prediction-system
設定環境變數
bash
echo "GROQ_API_KEY=your_api_key_here" > backend/.env
啟動服務
bash
cd backend
docker compose up -d
訪問應用
前端：http://localhost:3000
後端 API：http://localhost:8000/docs
📊 預測模型
評分維度：歷史戰績 (40%)、主客場優勢 (30%)、近期狀態 (20%)、進攻能力 (10%)

AI 分析流程：預測結果 → Groq API → Llama 3.3 70B → 繁體中文分析報告

📂 專案結構
Code
football-prediction-system/
├── backend/
│   ├── app/              # FastAPI 應用
│   ├── scripts/          # 預測腳本
│   └── data/             # 數據檔案
└── frontend/
    ├── app/              # Next.js 頁面
    └── components/       # React 元件
🎯 API 端點
GET /api/predictions?league=Premier%20League - 獲取預測
GET /api/teams/Arsenal - 獲取球隊詳情
完整文檔：http://localhost:8000/docs
🔮 未來規劃
 自動更新賽程
 歷史預測準確率追蹤
 用戶帳號系統
 多語言支援
📈 專案統計
程式碼：6071 行新增，520 行刪除
檔案：53 個檔案修改
比賽預測：47 場（五大聯賽）
AI 分析覆蓋率：100%
📄 授權
MIT License

👨‍💻 作者
tsoAI0305 - GitHub: @tsoAI0305

🙏 致謝
Groq - 提供高速 AI 推理
FastAPI - 現代化 Python Web 框架
Next.js - React 全棧框架
⭐ 如果這個專案對你有幫助，請給個 Star！ 

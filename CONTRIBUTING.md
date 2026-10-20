# 🤝 貢獻指南

感謝你對 AI 足球預測系統的興趣！

## 📋 如何貢獻

### 🐛 報告 Bug
前往 Issues 頁面描述問題

### 💡 建議新功能
開啟 Issue 並標註 enhancement

### 🔧 提交程式碼
1. Fork 專案
2. 建立分支: git checkout -b feature/your-feature
3. 提交修改: git commit -m "feat: 描述"
4. 推送並開 PR

## 🛠️ 開發環境

### 一鍵起整站（建議）
在 repo 根目錄：`docker compose up --build`

### 後端（本機）
cd backend && python -m venv venv && pip install -r requirements.txt

### 前端（本機，若不用 compose 的 web）
cd frontend && npm install && npm run dev

## 📝 分支與提交（圖才好看）

顏色只是 Git Graph 用來區分同時存在的線，沒有「橘=Phase 1」這種意思。

- `main`：已合併的主線
- 一條功能分支做完再開 PR，**不要一個 phase 開一條 branch**
- 準確率主線用 `feat/accuracy-roadmap`，每個 phase 一個 commit，訊息帶 phase 前綴

```
feat(phase0-boot): ...
feat(phase0): ...
feat(phase1): ...
feat(phase1b): ...
```

這樣圖上同一條彩色線、點旁邊就能看出做到哪一階段。

## 📝 提交訊息規範
feat: 新功能
fix: 修復
docs: 文檔
style: 格式
refactor: 重構
test: 測試

## 🙋 需要協助
Issues: https://github.com/tsoAI0305/football-prediction-system/issues
維護者: @tsoAI0305

⭐ 歡迎 Star 和貢獻！

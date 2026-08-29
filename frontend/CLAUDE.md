# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

This is a monorepo with two independent sub-projects:

```
football-prediction-system/
├── frontend/   ← Next.js 16 / React 19 / TypeScript (this directory)
└── backend/    ← FastAPI / Python 3.11+ / PostgreSQL / Redis
```

## Frontend commands

```bash
# Development server (http://localhost:3000)
npm run dev

# Production build
npm run build

# Lint
npm run lint
```

There is no test suite in the frontend yet.

## Backend commands

Run from `../backend/`:

```bash
# Full stack from repo root (frontend :3000 + API :8000 + Postgres + Redis)
docker compose up --build

# Legacy: cd backend && docker compose up  (includes the root compose)

# Local dev (requires DB and Redis already running)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run all tests
pytest tests/ -v

# Run a single test
pytest tests/test_ml_service.py::test_predict_from_dataframe_odds_fallback -v

# Coverage report
pytest tests/ --cov=app --cov-report=html

# Generate next-week predictions (writes data/final_predictions.json)
python scripts/predict_next_week.py

# Train the ML model (requires sufficient historical data in DB)
python scripts/train_model.py
```

Backend environment variables go in `backend/.env` (copy from `.env.example`). Key vars:

```
DATABASE_URL=postgresql://football_user:football_pass@localhost:5432/football_db
REDIS_URL=redis://localhost:6379/0
LLM_API_KEY=<groq-key>
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.1-70b-versatile
```

## Architecture

### Data flow (prediction pipeline)

```
Sofascore / Sportsgambler scrapers
        ↓  (CSV → data/)
ingest_sofascore_csv.py → DB (matches table)
        ↓
feature_engineer.build_feature_matrix()
  - standings from data/top5_standings_latest.csv
  - injuries from data/*_teams_injuries_sportsgambler.csv
  - key-player injury alerts from data/*_injury_alert_report.csv
  - top players from data/*_team_top_players_sofascore_std.csv
  - DB historical form (last-5 / home/away win rates)
        ↓
MLService.predict_from_dataframe()
  - ensemble: GradientBoosting + RandomForest + LogisticRegression (soft voting)
  - model saved to models/ensemble_model.pkl
  - falls back to odds-derived probs when model file absent
        ↓
data/final_predictions.json   ← consumed by /api/predictions/ endpoints
```

The backend API serves `final_predictions.json` directly from disk; it does **not** call the ML model at request time. The ML pipeline is run offline via `scripts/predict_next_week.py`.

### Backend structure

- `app/config.py` — Pydantic `Settings` (reads `.env`); `settings` singleton imported everywhere.
- `app/database.py` — SQLAlchemy engine + `SessionLocal` + `Base`; `get_db()` FastAPI dependency.
- `app/models/` — SQLAlchemy ORM: `Match`, `Prediction` (with `PredictionResult` enum H/D/A), `Team`.
- `app/routers/predictions.py` — serves predictions from JSON; `/{match_id}` triggers LLM analysis (Groq) and caches result in `Prediction` DB table.
- `app/services/feature_engineer.py` — `build_feature_matrix(fixtures_df, db)` produces the 40-column feature DataFrame.
- `app/services/ml_service.py` — `MLService`: `train(df)`, `predict_from_dataframe(df)`. Loads `models/ensemble_model.pkl` (dict with `model`, `label_encoder`, `feature_cols`).
- `app/services/llm_service.py` — wraps Groq/OpenAI-compatible API for narrative match analysis.
- `app/utils/cache.py` — Redis cache helpers.
- `scripts/` — one-off data fetch / ingest / predict scripts; not imported by the app.
- `tests/` — pytest; no DB required for unit tests (they mock or use in-memory data).

### Frontend structure

- **All pages are client components** (`'use client'`).
- `lib/api.ts` — single axios instance (`API_BASE_URL` = `NEXT_PUBLIC_API_URL || localhost:8000`), `predictionService` object + standalone `getHistory` / `getTeamMatches` functions. **This is the only file that talks to the backend.**
- `lib/types.ts` — legacy type definitions (less complete than the inline types in `lib/api.ts`; prefer `api.ts` types for new code).
- `app/page.tsx` and `app/history/page.tsx` are currently identical (the history page is a stub that uses the same component). This is a known issue.
- `components/PredictionCard.tsx` — the primary display component; it lazily fetches team stats via `getTeamMatches` on expand. Sub-components `TeamDetailPanel` and `MatchAnalysisPanel` are defined in the same file.
- `components/Header.tsx` — standalone header (not `Navbar`). `layout.tsx` renders `Navbar`; individual pages render `Header`. These serve different roles.

### Prediction data shape

The canonical prediction object (from `final_predictions.json` and `lib/api.ts`):

```ts
{
  match_id: number,
  league: string,
  date: string,        // "YYYY-MM-DD"
  time: string,        // "HH:MM"
  home_team: string,
  away_team: string,
  prediction: {
    prediction: 'H' | 'D' | 'A',
    confidence: number,      // 0–1
    home_win_prob: number,
    draw_prob: number,
    away_win_prob: number,
    over25_prob: number,
    under25_prob: number,
    ou_pick: 'OVER' | 'UNDER',
    betting_advice: string,
  },
  generated_at: string,
}
```

## Key constraints

- Static routes in `app/routers/predictions.py` (`/leagues`, `/teams`, `/stats`) **must** be defined before the dynamic `/{match_id}` route or FastAPI will swallow them.
- `MLService._compute_probs` returns probabilities in **H, D, A** order. The LabelEncoder inside the saved model uses **A=0, D=1, H=2** order — the re-indexing in `_compute_probs` is intentional.
- Team name matching across CSV sources uses `_std_name()` (lowercase, strip non-alphanumeric). When debugging join misses, always check that both sides went through `_std_name`.
- `app/config.py` has `extra = "allow"` so unknown env vars don't crash startup.

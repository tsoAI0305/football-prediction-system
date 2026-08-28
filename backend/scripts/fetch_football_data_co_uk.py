"""
scripts/fetch_football_data_co_uk.py

自動下載 football-data.co.uk 五大聯賽最新數據
並 upsert 進 DB（補充比分、賠率、射門、角球等詳細統計）

執行：
    cd D:\football-prediction-system\backend
    python scripts/fetch_football_data_co_uk.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
import io
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from app.database import SessionLocal
from app.models.match import Match

# ── 聯賽設定 ──────────────────────────────────────────────────────────────────
LEAGUES = [
    {"file": "E0",  "league": "Premier League", "season": "2526"},
    {"file": "D1",  "league": "Bundesliga",      "season": "2526"},
    {"file": "SP1", "league": "La Liga",         "season": "2526"},
    {"file": "I1",  "league": "Serie A",         "season": "2526"},
    {"file": "F1",  "league": "Ligue 1",         "season": "2526"},
]

BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/{file}.csv"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# ── 球隊名稱對應（football-data → sofascore 名稱）────────────────────────────
# 如有對不上的球隊再補充
TEAM_NAME_MAP = {
    # EPL
    "Man United":    "Manchester United",
    "Man City":      "Manchester City",
    "Newcastle":     "Newcastle United",
    "Nott'm Forest": "Nottingham Forest",
    "Wolves":        "Wolverhampton Wanderers",
    "Spurs":         "Tottenham",
    # Bundesliga
    "Bayern Munich": "FC Bayern München",
    "Leverkusen":    "Bayer Leverkusen",
    "Dortmund":      "Borussia Dortmund",
    "M'gladbach":    "Borussia Mönchengladbach",
    "Ein Frankfurt": "Eintracht Frankfurt",
    "Werder Bremen": "Werder Bremen",
    # La Liga
    "Ath Madrid":    "Atlético Madrid",
    "Ath Bilbao":    "Athletic Club",
    "Betis":         "Real Betis",
    "Espanol":       "Espanyol",
    "Vallecano":     "Rayo Vallecano",
    # Serie A
    "Inter":         "Inter Milan",
    "AC Milan":      "Milan",
    "Verona":        "Hellas Verona",
    # Ligue 1
    "Paris SG":      "Paris Saint-Germain",
    "St Etienne":    "Saint-Étienne",
    "Marseille":     "Olympique de Marseille",
    "Lyon":          "Olympique Lyonnais",
}

def normalize_team(name: str) -> str:
    return TEAM_NAME_MAP.get(name.strip(), name.strip())

def parse_date(s: str) -> datetime | None:
    """football-data 日期格式 YYYY/MM/DD 或 DD/MM/YY"""
    for fmt in ("%Y/%m/%d", "%d/%m/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            continue
    return None

def to_float(val) -> float | None:
    try:
        f = float(val)
        return f if f > 0 else None
    except (ValueError, TypeError):
        return None

def to_int(val) -> int | None:
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None

def download_csv(league: dict) -> pd.DataFrame | None:
    url = BASE_URL.format(season=league["season"], file=league["file"])
    print(f"  ⬇️  下載 {url}")
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        # football-data.co.uk 有時用 latin-1
        content = resp.content.decode("latin-1")
        df = pd.read_csv(io.StringIO(content))
        # 只保留有效行（HomeTeam 不為空）
        df = df[df["HomeTeam"].notna() & (df["HomeTeam"] != "")]
        print(f"     → {len(df)} 筆記錄")
        return df
    except Exception as e:
        print(f"  ❌ 下載失敗：{e}")
        return None

def save_local(df: pd.DataFrame, league: dict) -> None:
    """同時存一份到 data/ 資料夾"""
    fname = DATA_DIR / f"{league['file']}_{league['season']}.csv"
    df.to_csv(fname, index=False)
    print(f"     💾 已存至 {fname}")

def upsert_league(df: pd.DataFrame, league_name: str, db) -> dict:
    created = updated = skipped = 0

    for _, row in df.iterrows():
        home = normalize_team(str(row.get("HomeTeam", "")))
        away = normalize_team(str(row.get("AwayTeam", "")))
        dt   = parse_date(str(row.get("Date", "")))

        if not home or not away or not dt:
            skipped += 1
            continue

        # 比分
        home_score = to_int(row.get("FTHG"))
        away_score = to_int(row.get("FTAG"))
        ftr        = str(row.get("FTR", "")).strip()  # H / D / A

        # 比賽統計
        home_shots    = to_int(row.get("HS"))
        away_shots    = to_int(row.get("AS"))
        home_sot      = to_int(row.get("HST"))
        away_sot      = to_int(row.get("AST"))
        home_corners  = to_int(row.get("HC"))
        away_corners  = to_int(row.get("AC"))
        home_fouls    = to_int(row.get("HF"))
        away_fouls    = to_int(row.get("AF"))
        home_yellow   = to_int(row.get("HY"))
        away_yellow   = to_int(row.get("AY"))
        home_red      = to_int(row.get("HR"))
        away_red      = to_int(row.get("AR"))

        # 賠率
        b365_h = to_float(row.get("B365H"))
        b365_d = to_float(row.get("B365D"))
        b365_a = to_float(row.get("B365A"))
        avg_h  = to_float(row.get("AvgH"))
        avg_d  = to_float(row.get("AvgD"))
        avg_a  = to_float(row.get("AvgA"))

        # 先精確比對，再同日比對
        existing = db.query(Match).filter(
            Match.home_team  == home,
            Match.away_team  == away,
            Match.match_date == dt,
        ).first()

        if not existing:
            existing = db.query(Match).filter(
                Match.home_team  == home,
                Match.away_team  == away,
                Match.match_date >= dt.replace(hour=0,  minute=0),
                Match.match_date <= dt.replace(hour=23, minute=59),
            ).first()

        if existing:
            changed = False
            # 比分（優先 football-data，因為有賽果）
            if home_score is not None:
                existing.home_score = home_score; changed = True
            if away_score is not None:
                existing.away_score = away_score; changed = True
            if ftr in ("H", "D", "A"):
                existing.status = "FINISHED"; changed = True

            # 統計數據（只在 DB 無值時填入）
            def fill(attr, val):
                nonlocal changed
                if val is not None and getattr(existing, attr) is None:
                    setattr(existing, attr, val); changed = True

            fill("home_shots",            home_shots)
            fill("away_shots",            away_shots)
            fill("home_shots_on_target",  home_sot)
            fill("away_shots_on_target",  away_sot)
            fill("home_corners",          home_corners)
            fill("away_corners",          away_corners)
            fill("home_fouls",            home_fouls)
            fill("away_fouls",            away_fouls)
            fill("home_yellow",           home_yellow)
            fill("away_yellow",           away_yellow)
            fill("home_red",              home_red)
            fill("away_red",              away_red)

            # 賠率（總是用最新值覆蓋）
            if b365_h: existing.b365_home  = b365_h; changed = True
            if b365_d: existing.b365_draw  = b365_d; changed = True
            if b365_a: existing.b365_away  = b365_a; changed = True
            if avg_h:  existing.avg_home   = avg_h;  changed = True
            if avg_d:  existing.avg_draw   = avg_d;  changed = True
            if avg_a:  existing.avg_away   = avg_a;  changed = True

            if changed:
                updated += 1
        else:
            # 新增（football-data 有的但 sofascore 沒爬到的場次）
            db.add(Match(
                league     = league_name,
                match_date = dt,
                home_team  = home,
                away_team  = away,
                home_score = home_score,
                away_score = away_score,
                status     = "FINISHED" if ftr in ("H","D","A") else "SCHEDULED",
                home_shots = home_shots, away_shots = away_shots,
                home_shots_on_target = home_sot, away_shots_on_target = away_sot,
                home_corners = home_corners, away_corners = away_corners,
                home_fouls   = home_fouls,   away_fouls   = away_fouls,
                home_yellow  = home_yellow,  away_yellow  = away_yellow,
                home_red     = home_red,     away_red     = away_red,
                b365_home = b365_h, b365_draw = b365_d, b365_away = b365_a,
                avg_home  = avg_h,  avg_draw  = avg_d,  avg_away  = avg_a,
            ))
            created += 1

    db.commit()
    return {"created": created, "updated": updated, "skipped": skipped}


def main():
    print("=" * 55)
    print("⬇️  football-data.co.uk 自動下載 + upsert")
    print("=" * 55)

    db = SessionLocal()
    total = {"created": 0, "updated": 0, "skipped": 0}

    try:
        for league in LEAGUES:
            print(f"\n【{league['league']}】")
            df = download_csv(league)
            if df is None:
                continue

            save_local(df, league)

            print(f"  🔄 upsert 進 DB...")
            result = upsert_league(df, league["league"], db)
            for k in total:
                total[k] += result.get(k, 0)
            print(f"  ✅ created={result['created']}  "
                  f"updated={result['updated']}  "
                  f"skipped={result['skipped']}")

        print(f"\n{'='*55}")
        print(f"✅ 完成！"
              f"created={total['created']}  "
              f"updated={total['updated']}  "
              f"skipped={total['skipped']}")

        # 確認比賽統計填充情況
        from sqlalchemy import func
        shots_filled = db.query(Match).filter(Match.home_shots.isnot(None)).count()
        odds_filled  = db.query(Match).filter(Match.b365_home.isnot(None)).count()
        total_m      = db.query(Match).count()
        print(f"\n📊 DB 統計：")
        print(f"   總比賽數: {total_m}")
        print(f"   有射門數據: {shots_filled} 場")
        print(f"   有賠率數據: {odds_filled} 場")

    except Exception as e:
        db.rollback()
        print(f"\n❌ 錯誤: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
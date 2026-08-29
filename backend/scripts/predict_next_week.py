"""
scripts/predict_next_week.py

從 DB 取未來 14 天賽程 → feature_engineer → ml_service
→ 輸出 data/final_predictions.json（供 /api/predictions/ 讀取）
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from app.database import SessionLocal
from app.models.match import Match
from app.services.feature_engineer import add_diff_features, build_feature_matrix
from app.services.ml_service import MLService


def add_diff_features(df: pd.DataFrame) -> pd.DataFrame:
    if "home_rank" in df.columns and "away_rank" in df.columns:
        df["rank_diff"]   = df["home_rank"]      - df["away_rank"]
        df["points_diff"] = df["home_points"]    - df["away_points"]
        df["gd_diff"]     = df["home_goal_diff"] - df["away_goal_diff"]
    return df


def betting_advice(pred: str, conf: float,
                   ph: float, pd_: float, pa: float,
                   over_p: float) -> str:
    """產生投注建議文字"""
    result_map = {"H": "主勝", "D": "平局", "A": "客勝"}
    ou_str = f"大球({over_p:.0%})" if over_p >= 0.5 else f"小球({1-over_p:.0%})"

    if conf >= 0.70:
        return f"強烈推薦：{result_map[pred]}（{conf:.0%}）+ {ou_str}"
    elif conf >= 0.55:
        return f"建議：{result_map[pred]}（{conf:.0%}）+ {ou_str}"
    else:
        return f"參考：{result_map[pred]}（{conf:.0%}），{ou_str}，建議觀望"


def main():
    days_ahead = int(os.environ.get("PREDICT_DAYS", 14))
    now = datetime.utcnow()
    cutoff = now + timedelta(days=days_ahead)

    print(f"🔮 預測未來 {days_ahead} 天比賽（至 {cutoff.date()}）")

    db = SessionLocal()
    try:
        upcoming = (
            db.query(Match)
            .filter(
                Match.status == "SCHEDULED",
                Match.match_date >= now,
                Match.match_date <= cutoff,
            )
            .order_by(Match.match_date)
            .all()
        )
        print(f"📅 找到 {len(upcoming)} 場未來賽程")

        if not upcoming:
            print("❌ 沒有未來賽程，請確認 DB 已 ingest 賽程"); return

        # ── Feature matrix ─────────────────────────────────────────────
        up_df = pd.DataFrame([{
            "match_id":   m.id,
            "home_team":  m.home_team,
            "away_team":  m.away_team,
            "league":     m.league,
            "season":     m.season,
            "match_date": m.match_date,
        } for m in upcoming])

        feat_df = add_diff_features(build_feature_matrix(up_df, db=db))

        # ── 勝平負預測 ──────────────────────────────────────────────────
        svc = MLService()
        if svc.model is None:
            print("⚠️  models/ensemble_model.pkl 不存在，請先跑 train_model.py")
            return
        result_preds = svc.predict_from_dataframe(feat_df)

        # ── 大小球預測 ──────────────────────────────────────────────────
        ou_path = Path("models/ou_model.pkl")
        if ou_path.exists():
            ou_pay  = joblib.load(ou_path)
            ou_mod  = ou_pay["model"]
            avail   = [c for c in ou_pay["feature_cols"] if c in feat_df.columns]
            ou_probs = ou_mod.predict_proba(feat_df[avail].fillna(0).values)
        else:
            print("⚠️  ou_model.pkl 不存在，大小球以 50% 填充")
            ou_probs = np.full((len(feat_df), 2), 0.5)

        # ── 組合輸出 ────────────────────────────────────────────────────
        match_map = {m.id: m for m in upcoming}
        output = []

        for i, (_, row) in enumerate(result_preds.iterrows()):
            mid   = int(row["match_id"])
            m     = match_map.get(mid)
            if not m: continue

            ph    = round(float(row["predicted_home_win_prob"]), 3)
            pd_   = round(float(row["predicted_draw_prob"]),     3)
            pa    = round(float(row["predicted_away_win_prob"]), 3)
            pred  = str(row["prediction"])
            conf  = round(float(row["confidence"]), 3)
            over_p = round(float(ou_probs[i][1]), 3)

            output.append({
                "match_id":   mid,
                "league":     m.league,
                "date":       m.match_date.strftime("%Y-%m-%d"),
                "time":       m.match_date.strftime("%H:%M"),
                "home_team":  m.home_team,
                "away_team":  m.away_team,
                "prediction": {
                    # 勝平負
                    "prediction":   pred,          # H / D / A
                    "confidence":   conf,
                    "home_win_prob": ph,
                    "draw_prob":    pd_,
                    "away_win_prob": pa,
                    # 大小球
                    "over25_prob":  over_p,
                    "under25_prob": round(1 - over_p, 3),
                    "ou_pick":      "OVER" if over_p >= 0.5 else "UNDER",
                    # 投注建議
                    "betting_advice": betting_advice(pred, conf, ph, pd_, pa, over_p),
                },
                "generated_at": datetime.utcnow().isoformat(),
            })

        # ── 寫入 JSON ───────────────────────────────────────────────────
        out_path = Path("data/final_predictions.json")
        out_path.parent.mkdir(exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 已輸出 {len(output)} 場預測 → {out_path}")

        # 摘要
        from collections import Counter
        pred_dist = Counter(o["prediction"]["prediction"] for o in output)
        ou_dist   = Counter(o["prediction"]["ou_pick"] for o in output)
        print(f"   勝平負分佈：H={pred_dist['H']}  D={pred_dist['D']}  A={pred_dist['A']}")
        print(f"   大小球分佈：OVER={ou_dist['OVER']}  UNDER={ou_dist['UNDER']}")

        # 印前5筆
        print("\n📋 前5場預測：")
        for o in output[:5]:
            p = o["prediction"]
            print(f"  [{o['league']}] {o['date']} {o['time']}  "
                  f"{o['home_team']} vs {o['away_team']}")
            print(f"    → {p['prediction']}({p['confidence']:.0%})  "
                  f"{p['ou_pick']}({p['over25_prob']:.0%})  {p['betting_advice']}")

    finally:
        db.close()


if __name__ == "__main__":
    main()

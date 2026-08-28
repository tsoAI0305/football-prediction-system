"""
scripts/train_model.py  (v2)
同時訓練：1) 勝平負  2) 大小球(O/U 2.5)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from app.database import SessionLocal
from app.models.match import Match
from app.services.feature_engineer import build_feature_matrix
from app.services.ml_service import MLService, FEATURE_COLS


def load_training_data(db):
    matches = (
        db.query(Match)
        .filter(Match.status=="FINISHED",
                Match.home_score.isnot(None),
                Match.away_score.isnot(None))
        .order_by(Match.match_date.desc()).all()
    )
    print(f"📊 DB 有比分比賽：{len(matches)} 場")
    rows = []
    for m in matches:
        if not m.home_team or not m.away_team: continue
        total = m.home_score + m.away_score
        rows.append({
            "match_id": m.id, "home_team": m.home_team, "away_team": m.away_team,
            "league": m.league, "match_date": m.match_date,
            "home_score": m.home_score, "away_score": m.away_score,
            "result": "H" if m.home_score>m.away_score else ("A" if m.away_score>m.home_score else "D"),
            "total_goals": total, "over25": int(total > 2.5),
        })
    return pd.DataFrame(rows)


def train_ou_model(feat_df):
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    from sklearn.model_selection import cross_val_score

    df = feat_df.dropna(subset=["over25"]).copy()
    available = [c for c in FEATURE_COLS if c in df.columns]
    X = df[available].fillna(0).values
    y = df["over25"].astype(int).values
    over_rate = y.mean()
    print(f"   大球比例: {over_rate*100:.1f}%")

    ensemble = VotingClassifier(estimators=[
        ("gb", GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42)),
        ("rf", RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)),
        ("lr", make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=5000, solver="saga", random_state=42))),
    ], voting="soft")
    ensemble.fit(X, y)
    cv = cross_val_score(ensemble, X, y, cv=5, scoring="accuracy")

    Path("models").mkdir(exist_ok=True)
    joblib.dump({"model": ensemble, "feature_cols": available, "over_rate": float(over_rate)},
                "models/ou_model.pkl")
    return {"cv_accuracy": round(float(cv.mean()),4), "cv_std": round(float(cv.std()),4)}


def add_diff_features(df):
    if "home_rank" in df.columns and "away_rank" in df.columns:
        df["rank_diff"]   = df["home_rank"]      - df["away_rank"]
        df["points_diff"] = df["home_points"]    - df["away_points"]
        df["gd_diff"]     = df["home_goal_diff"] - df["away_goal_diff"]
    return df


def main():
    print("="*55)
    print("🏋️  訓練預測模型（勝平負 + 大小球）")
    print("="*55)

    db = SessionLocal()
    try:
        hist_df = load_training_data(db)
        if hist_df.empty: print("❌ 無資料"); return

        print("\n⚙️  建立 feature matrix...")
        feat_df = build_feature_matrix(hist_df, db=db)
        feat_df["result"]      = hist_df["result"].values
        feat_df["over25"]      = hist_df["over25"].values
        feat_df["total_goals"] = hist_df["total_goals"].values
        feat_df = add_diff_features(feat_df)

        print("\n🤖 訓練勝平負模型...")
        svc = MLService()
        r1 = svc.train(feat_df)
        print(f"   ✅ CV: {r1['cv_accuracy']*100:.1f}% ± {r1['cv_std']*100:.1f}%")

        print("\n⚽ 訓練大小球模型...")
        r2 = train_ou_model(feat_df)
        print(f"   ✅ CV: {r2['cv_accuracy']*100:.1f}% ± {r2['cv_std']*100:.1f}%")

        print(f"\n{'='*55}")
        print(f"✅ 完成！勝平負:{r1['cv_accuracy']*100:.1f}%  大小球:{r2['cv_accuracy']*100:.1f}%")

        # 快速測試
        print("\n🔮 測試未來 5 場...")
        upcoming = db.query(Match).filter(Match.status=="SCHEDULED").order_by(Match.match_date).limit(5).all()
        if upcoming:
            up_df = pd.DataFrame([{"match_id":m.id,"home_team":m.home_team,"away_team":m.away_team,
                                    "league":m.league,"match_date":m.match_date} for m in upcoming])
            feat_up = add_diff_features(build_feature_matrix(up_df, db=db))

            svc2   = MLService()
            preds  = svc2.predict_from_dataframe(feat_up)
            ou_pay = joblib.load("models/ou_model.pkl")
            avail  = [c for c in ou_pay["feature_cols"] if c in feat_up.columns]
            ou_p   = ou_pay["model"].predict_proba(feat_up[avail].fillna(0).values)

            for i, (_, row) in enumerate(preds.iterrows()):
                m = next((x for x in upcoming if x.id==int(row["match_id"])), None)
                op = float(ou_p[i][1])
                ou_str = f"大球({op:.0%})" if op>=0.5 else f"小球({1-op:.0%})"
                if m:
                    print(f"  {m.home_team:25s} vs {m.away_team:25s} "
                          f"→ {row['prediction']}({row['confidence']:.2f})  {ou_str}")
    finally:
        db.close()

if __name__ == "__main__":
    main()

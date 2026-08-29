"""
Walk-forward check: train on seasons before hold-out, test on 2526.

Compares the as-of ensemble to a B365 implied-probability baseline.
Only rows with B365 are scored so the comparison is fair.

  docker compose exec api python scripts/evaluate_walk_forward.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from sklearn.metrics import accuracy_score, log_loss

from app.database import SessionLocal
from app.models.match import Match, MatchStatus
from app.services.feature_engineer import build_feature_matrix, implied_probs
from app.services.ml_service import MLService
import pandas as pd


def load_training_data(db):
    matches = (
        db.query(Match)
        .filter(
            Match.status == MatchStatus.FINISHED.value,
            Match.home_score.isnot(None),
            Match.away_score.isnot(None),
        )
        .order_by(Match.match_date.asc())
        .all()
    )
    rows = []
    for m in matches:
        if not m.home_team or not m.away_team:
            continue
        total = m.home_score + m.away_score
        rows.append({
            "match_id": m.id,
            "home_team": m.home_team,
            "away_team": m.away_team,
            "league": m.league,
            "season": m.season,
            "match_date": m.match_date,
            "home_score": m.home_score,
            "away_score": m.away_score,
            "b365_home": m.b365_home,
            "b365_draw": m.b365_draw,
            "b365_away": m.b365_away,
            "result": "H" if m.home_score > m.away_score else ("A" if m.away_score > m.home_score else "D"),
            "total_goals": total,
        })
    return pd.DataFrame(rows)

HOLD_OUT = "2526"


def _labels(series):
    return series.map({"H": 0, "D": 1, "A": 2}).astype(int)


def _odds_matrix(df):
    rows = []
    for _, r in df.iterrows():
        rows.append(implied_probs(r.get("b365_home"), r.get("b365_draw"), r.get("b365_away")))
    return np.array(rows)


def _report(name, y, proba) -> dict:
    pred = np.argmax(proba, axis=1)
    acc = float(accuracy_score(y, pred))
    ll = float(log_loss(y, proba, labels=[0, 1, 2]))
    print(f"  {name:18s}  accuracy={acc:.3f}  log_loss={ll:.3f}  n={len(y)}")
    return {"name": name, "accuracy": acc, "log_loss": ll, "n": len(y)}


def main():
    db = SessionLocal()
    try:
        hist = load_training_data(db)
        print(f"loaded {len(hist)} FINISHED rows")
        hist["season"] = hist["season"].astype(str)
        train_raw = hist[hist["season"] != HOLD_OUT].copy()
        test_raw = hist[hist["season"] == HOLD_OUT].copy()
        test_raw = test_raw[test_raw["b365_home"].notna() & test_raw["b365_draw"].notna() & test_raw["b365_away"].notna()]
        print(f"train seasons != {HOLD_OUT}: {len(train_raw)}")
        print(f"test  {HOLD_OUT} with B365: {len(test_raw)}")
        if len(train_raw) < 50 or len(test_raw) < 50:
            raise SystemExit("not enough rows for walk-forward")

        print("building as-of features (train + test)...")
        feat_train = build_feature_matrix(train_raw, db=db)
        feat_train["result"] = train_raw["result"].values
        feat_test = build_feature_matrix(test_raw, db=db)
        feat_test["result"] = test_raw["result"].values
        feat_test["b365_home"] = test_raw["b365_home"].values
        feat_test["b365_draw"] = test_raw["b365_draw"].values
        feat_test["b365_away"] = test_raw["b365_away"].values

        svc = MLService(model_path="models/ensemble_walkforward.pkl")
        stats = svc.train(feat_train)
        print(f"fit n={stats['n_samples']} (random CV is not the hold-out score)")

        preds = svc.predict_from_dataframe(feat_test)
        model_p = np.column_stack(
            [
                preds["predicted_home_win_prob"],
                preds["predicted_draw_prob"],
                preds["predicted_away_win_prob"],
            ]
        )
        y = _labels(feat_test["result"]).to_numpy()
        odds_p = _odds_matrix(feat_test)

        print(f"\nwalk-forward hold-out {HOLD_OUT} (B365 rows only)")
        model = _report("model", y, model_p)
        base = _report("B365 implied", y, odds_p)
        acc_win = model["accuracy"] > base["accuracy"]
        ll_win = model["log_loss"] < base["log_loss"]
        print(
            f"\nbeats odds on accuracy: {acc_win}   "
            f"beats odds on log_loss: {ll_win}"
        )
        if not (acc_win or ll_win):
            print("did not beat the market — inspect leakage and team-name joins before adding features")
            sys.exit(2)
    finally:
        db.close()


if __name__ == "__main__":
    main()

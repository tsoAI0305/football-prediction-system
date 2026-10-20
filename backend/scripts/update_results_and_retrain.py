"""
scripts/update_results_and_retrain.py

ML 回饋循環主控腳本 ─ 四步驟自動化流程：
  A  從 football-data.co.uk 抓取最新賽果 → upsert DB
  B  同步 Prediction 表實際結果 + 匯出訓練快照 CSV
  C  備份舊模型 → 重訓 ensemble_model.pkl + ou_model.pkl
  D  重新生成下周預測（data/final_predictions.json）

用法（請從 backend/ 目錄執行）：
  python scripts/update_results_and_retrain.py
  python scripts/update_results_and_retrain.py --skip-predict   # 只重訓，不更新預測
  python scripts/update_results_and_retrain.py --skip-fetch     # 不抓新資料，只重訓
  python scripts/update_results_and_retrain.py --dry-run        # 預覽所有步驟，不寫任何東西

前置條件：
  1. 已執行過 init_db.py 建立資料庫
  2. 已有至少一輪的 sofascore CSV 導入（ingest_sofascore_csv.py）
  3. models/ 目錄已存在第一版模型（由 train_model.py 產生）
"""
import sys
import os

# 讓 app.* 可以被 import，無論從哪個目錄執行此腳本
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import argparse
import json
import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import or_

from app.database import SessionLocal
from app.models.match import Match
from app.models.prediction import Prediction, PredictionResult

# ── 路徑常數 ──────────────────────────────────────────────────────────────────
BASE_DIR         = Path(_BACKEND)
SCRIPTS_DIR      = BASE_DIR / "scripts"
DATA_DIR         = BASE_DIR / "data"
MODELS_DIR       = BASE_DIR / "models"
BACKUP_DIR       = MODELS_DIR / "backups"
PREDICTIONS_FILE = DATA_DIR / "final_predictions.json"
SNAPSHOT_DIR     = DATA_DIR / "training_snapshots"

# ── 日誌設定 ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# 共用工具
# ══════════════════════════════════════════════════════════════════════════════

def _banner(text: str) -> None:
    log.info("=" * 62)
    log.info(f"  {text}")
    log.info("=" * 62)


def _run_script(script_name: str, extra_args: list | None = None, dry_run: bool = False) -> bool:
    """以獨立子程序執行 scripts/ 中的腳本，回傳 True 表示成功。"""
    script_path = SCRIPTS_DIR / script_name
    cmd = [sys.executable, str(script_path)] + (extra_args or [])
    if dry_run:
        log.info(f"  [dry-run] 跳過：{' '.join(str(c) for c in cmd)}")
        return True
    log.info(f"  ▶  {' '.join(str(c) for c in cmd)}")
    # 強制子程序使用 UTF-8，避免 Windows cp950 console 無法顯示 emoji 而崩潰
    child_env = os.environ.copy()
    child_env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(cmd, cwd=str(BASE_DIR), env=child_env)
    if result.returncode != 0:
        log.error(f"  ❌ 腳本失敗（exit {result.returncode}）：{script_name}")
        return False
    return True


def _compute_actual(home: int, away: int) -> PredictionResult:
    if home > away:
        return PredictionResult.HOME_WIN
    if away > home:
        return PredictionResult.AWAY_WIN
    return PredictionResult.DRAW


# ══════════════════════════════════════════════════════════════════════════════
# A  抓取最新賽果
# ══════════════════════════════════════════════════════════════════════════════

def step_a_fetch_results(dry_run: bool) -> bool:
    """
    呼叫 fetch_football_data_co_uk.py：
    - 從 football-data.co.uk 下載五大聯賽最新 CSV
    - 儲存至 data/ 資料夾（E0_2526.csv 等）
    - Upsert 至 Match 表（更新 home_score / away_score / status）
    """
    _banner("A  抓取最新賽果（football-data.co.uk）")
    ok = _run_script("fetch_football_data_co_uk.py", dry_run=dry_run)
    if ok:
        log.info("✅ 步驟 A 完成：賽果已下載並 upsert 至 DB")
    return ok


# ══════════════════════════════════════════════════════════════════════════════
# B  同步 Prediction 表 + 匯出訓練快照
# ══════════════════════════════════════════════════════════════════════════════

def _sync_prediction_actuals(db, dry_run: bool) -> dict:
    """
    讀取 final_predictions.json，逐筆找對應的 Match 記錄：
    - 若比賽已完賽（有比分）：計算 actual_result / is_correct，
      更新現有 Prediction 記錄，或新建一筆。
    - 若比賽尚未完賽：跳過（pending）。

    回傳 {"updated", "created", "pending"} 統計。
    """
    if not PREDICTIONS_FILE.exists():
        log.warning("  final_predictions.json 不存在，跳過 Prediction 同步")
        return {"updated": 0, "created": 0, "pending": 0}

    with open(PREDICTIONS_FILE, "r", encoding="utf-8") as f:
        json_preds: list[dict] = json.load(f)

    log.info(f"  讀取到 {len(json_preds)} 筆 JSON 預測")

    updated = created = pending = ou_hit_count = ou_total = 0

    for jp in json_preds:
        match_id = jp.get("match_id")
        if match_id is None:
            pending += 1
            continue

        # 先嘗試以 Match.id 比對，再嘗試 api_fixture_id
        match: Optional[Match] = db.query(Match).filter(
            or_(Match.id == match_id, Match.api_fixture_id == match_id)
        ).first()

        if not match or match.home_score is None or match.away_score is None:
            pending += 1
            continue

        # 計算實際結果
        actual = _compute_actual(match.home_score, match.away_score)

        pred_detail = jp.get("prediction", {})
        pred_str    = pred_detail.get("prediction")  # "H" / "D" / "A"
        try:
            predicted = PredictionResult(pred_str)
        except (ValueError, TypeError):
            log.warning(f"  ⚠️  無法解析預測值 {pred_str!r}（match_id={match_id}），跳過")
            pending += 1
            continue

        is_correct = (actual == predicted)

        # 計算大小球命中（不寫入 DB，僅用於日誌統計）
        ou_pick = pred_detail.get("ou_pick")
        if ou_pick in ("OVER", "UNDER"):
            total_goals = match.home_score + match.away_score
            actual_ou   = "OVER" if total_goals > 2.5 else "UNDER"
            if ou_pick == actual_ou:
                ou_hit_count += 1
            ou_total += 1

        if dry_run:
            log.info(
                f"  [dry-run] match {match_id}: "
                f"預測={predicted.value} 實際={actual.value} "
                f"比分={match.home_score}-{match.away_score} "
                f"命中={'✓' if is_correct else '✗'}"
            )
            updated += 1
            continue

        # 更新或新建 Prediction 記錄
        existing: Optional[Prediction] = (
            db.query(Prediction).filter(Prediction.match_id == match.id).first()
        )
        if existing:
            existing.actual_result = actual
            existing.is_correct    = is_correct
            updated += 1
        else:
            db.add(Prediction(
                match_id         = match.id,
                predicted_result = predicted,
                confidence_home  = float(pred_detail.get("home_win_prob", 0.0)),
                confidence_draw  = float(pred_detail.get("draw_prob",     0.0)),
                confidence_away  = float(pred_detail.get("away_win_prob", 0.0)),
                ai_score         = round(float(pred_detail.get("confidence", 0.0)) * 10, 2),
                betting_advice   = pred_detail.get("betting_advice", ""),
                value_rating     = 0.0,
                actual_result    = actual,
                is_correct       = is_correct,
            ))
            created += 1

    if not dry_run:
        db.commit()

    if ou_total > 0:
        log.info(f"  大小球命中：{ou_hit_count}/{ou_total}（{ou_hit_count/ou_total*100:.1f}%）")

    return {"updated": updated, "created": created, "pending": pending}


def _export_training_snapshot(db, dry_run: bool) -> Optional[Path]:
    """
    將 DB 中所有已完賽比賽匯出為帶時戳的 CSV。
    此 CSV 為稽核/備份用途；train_model.py 直接讀 DB，不依賴此 CSV。
    """
    matches = (
        db.query(Match)
        .filter(
            Match.status      == "FINISHED",
            Match.home_score.isnot(None),
            Match.away_score.isnot(None),
        )
        .order_by(Match.match_date.desc())
        .all()
    )

    if not matches:
        log.warning("  DB 無完賽比賽，跳過訓練快照匯出")
        return None

    rows = []
    for m in matches:
        if not m.home_team or not m.away_team:
            continue
        total = m.home_score + m.away_score
        rows.append({
            "match_id":    m.id,
            "date":        m.match_date.strftime("%Y-%m-%d") if m.match_date else "",
            "league":      m.league or "",
            "home_team":   m.home_team,
            "away_team":   m.away_team,
            "home_score":  m.home_score,
            "away_score":  m.away_score,
            "result":      "H" if m.home_score > m.away_score else (
                           "A" if m.away_score > m.home_score else "D"),
            "total_goals": total,
            "over25":      int(total > 2.5),
        })

    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SNAPSHOT_DIR / f"training_snapshot_{ts}.csv"

    if dry_run:
        log.info(f"  [dry-run] 將匯出 {len(rows)} 筆訓練資料 → {path}")
        return path

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")
    log.info(f"  📄 訓練快照：{path}（{len(rows)} 筆）")
    return path


def step_b_sync_and_snapshot(dry_run: bool) -> bool:
    """步驟 B 主函式：同步 Prediction 表 + 匯出快照 CSV。"""
    _banner("B  同步 Prediction 表 + 匯出訓練快照")
    db = SessionLocal()
    try:
        sync = _sync_prediction_actuals(db, dry_run)
        log.info(
            f"  Prediction 同步：updated={sync['updated']}  "
            f"created={sync['created']}  pending（未完賽）={sync['pending']}"
        )

        # 印全局準確率（用 raw SQL 避免 ORM 選出可能不存在的欄位）
        try:
            from sqlalchemy import text as _sql
            total_done = db.execute(_sql(
                "SELECT COUNT(*) FROM predictions WHERE is_correct IS NOT NULL"
            )).scalar() or 0
            correct = db.execute(_sql(
                "SELECT COUNT(*) FROM predictions WHERE is_correct = TRUE"
            )).scalar() or 0
            if total_done > 0:
                log.info(
                    f"  📊 全局準確率：{correct}/{total_done}（{correct/total_done*100:.1f}%）"
                )
        except Exception as _e:
            log.warning(f"  準確率統計跳過（{_e}）")

        _export_training_snapshot(db, dry_run)
        log.info("✅ 步驟 B 完成")
        return True

    except Exception as exc:
        log.error(f"  ❌ 步驟 B 失敗：{exc}")
        if not dry_run:
            db.rollback()
        return False
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# C  備份 + 重訓模型
# ══════════════════════════════════════════════════════════════════════════════

def _backup_models(dry_run: bool) -> list[Path]:
    """
    在重訓前將現有 pkl 備份至 models/backups/，
    若重訓結果不理想可手動還原。
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backed: list[Path] = []

    for fname in ("ensemble_model.pkl", "ou_model.pkl"):
        src = MODELS_DIR / fname
        if not src.exists():
            log.warning(f"  ⚠️  備份跳過（不存在）：{fname}")
            continue
        stem = fname.replace(".pkl", "")
        dst  = BACKUP_DIR / f"{stem}_{ts}.pkl"
        if dry_run:
            log.info(f"  [dry-run] 備份 {fname} → {dst.name}")
        else:
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            log.info(f"  💾 備份：{dst.name}（{dst.stat().st_size // 1024} KB）")
        backed.append(dst)

    return backed


def step_c_retrain(dry_run: bool) -> bool:
    """步驟 C 主函式：備份舊模型 → 呼叫 train_model.py 重訓。"""
    _banner("C  備份舊模型 + 重新訓練")

    backed = _backup_models(dry_run)
    if backed:
        log.info(f"  已備份 {len(backed)} 個模型")

    ok = _run_script("train_model.py", dry_run=dry_run)

    if ok and not dry_run:
        log.info("  新模型檔案：")
        for fname in ("ensemble_model.pkl", "ou_model.pkl"):
            p = MODELS_DIR / fname
            if p.exists():
                log.info(f"    ✅ {fname}（{p.stat().st_size // 1024} KB）")
            else:
                log.warning(f"    ⚠️  {fname} 不存在（訓練可能失敗）")

    if ok:
        log.info("✅ 步驟 C 完成：模型重訓成功，下次預測將使用新版本")
    return ok


# ══════════════════════════════════════════════════════════════════════════════
# D  重新生成預測
# ══════════════════════════════════════════════════════════════════════════════

def step_d_predict(dry_run: bool) -> bool:
    """步驟 D 主函式：以新模型重新跑 predict_next_week.py。"""
    _banner("D  重新生成下周預測（使用新模型）")
    ok = _run_script("predict_next_week.py", dry_run=dry_run)
    if ok:
        if not dry_run and PREDICTIONS_FILE.exists():
            with open(PREDICTIONS_FILE, encoding="utf-8") as f:
                count = len(json.load(f))
            log.info(f"  📋 data/final_predictions.json 已更新（{count} 場預測）")
        log.info("✅ 步驟 D 完成")
    return ok


# ══════════════════════════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(
        description="ML 回饋循環：抓賽果 → 同步 DB → 重訓模型 → 更新預測",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--skip-fetch",   action="store_true",
                        help="跳過步驟 A（使用 DB 現有資料直接重訓）")
    parser.add_argument("--skip-predict", action="store_true",
                        help="跳過步驟 D（重訓後不更新 final_predictions.json）")
    parser.add_argument("--dry-run",      action="store_true",
                        help="預覽模式：印出所有步驟但不寫入任何檔案或 DB")
    args = parser.parse_args()

    start_time = datetime.now()
    results: dict[str, bool | None] = {
        "A_fetch":   None,
        "B_sync":    None,
        "C_retrain": None,
        "D_predict": None,
    }

    _banner("ML 回饋循環啟動" + ("（dry-run 預覽模式）" if args.dry_run else ""))
    log.info(f"  時間：{start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"  工作目錄：{BASE_DIR}")
    log.info(f"  選項：skip-fetch={args.skip_fetch}  "
             f"skip-predict={args.skip_predict}  dry-run={args.dry_run}")

    # ── A ────────────────────────────────────────────────────────────────────
    if args.skip_fetch:
        log.info("\n⏭  跳過步驟 A（--skip-fetch）")
        results["A_fetch"] = True
    else:
        results["A_fetch"] = step_a_fetch_results(args.dry_run)

    # ── B（無論 A 成功與否都執行，已有舊資料也值得同步）───────────────────────
    results["B_sync"] = step_b_sync_and_snapshot(args.dry_run)

    # ── C（B 失敗則跳過，避免以臟資料訓練）─────────────────────────────────
    if results["B_sync"]:
        results["C_retrain"] = step_c_retrain(args.dry_run)
    else:
        log.error("\n⚠️  步驟 B 失敗，跳過步驟 C 以避免使用不完整的資料重訓")
        results["C_retrain"] = False

    # ── D（C 成功才有意義）──────────────────────────────────────────────────
    if args.skip_predict:
        log.info("\n⏭  跳過步驟 D（--skip-predict）")
        results["D_predict"] = True
    elif results["C_retrain"]:
        results["D_predict"] = step_d_predict(args.dry_run)
    else:
        log.warning("\n⚠️  步驟 C 失敗，跳過步驟 D")
        results["D_predict"] = False

    # ── 最終摘要 ─────────────────────────────────────────────────────────────
    elapsed = (datetime.now() - start_time).seconds
    _banner("執行摘要")

    STEP_LABELS = {
        "A_fetch":   "A  抓取最新賽果",
        "B_sync":    "B  同步 Prediction + 快照",
        "C_retrain": "C  重訓 ensemble + ou 模型",
        "D_predict": "D  更新 final_predictions.json",
    }
    all_ok = True
    for key, label in STEP_LABELS.items():
        status = results[key]
        if status is True:
            icon = "✅"
        elif status is False:
            icon = "❌"
            all_ok = False
        else:
            icon = "⏭ "
        log.info(f"  {icon}  {label}")

    log.info(f"\n  總耗時：{elapsed}s")
    if all_ok:
        log.info("🎉  回饋循環完成！模型已更新，下次預測使用新版模型。")
    else:
        log.error("⚠️  部分步驟失敗，請查看上方日誌。")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

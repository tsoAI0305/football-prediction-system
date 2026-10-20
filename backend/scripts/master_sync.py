"""
scripts/master_sync.py

全自動數據同步主控腳本（Phase 4）

執行順序：
  Step 1: 抓取最新聯賽積分榜  → fetch_top5_standings.py
  Step 2: 抓取戰術陣型數據    → ingest_tactical_data.py
  Step 3: 抓取昨日賽果並重訓  → update_results_and_retrain.py
          (內含: 抓結果 → 同步DB → 重訓模型 → 更新預測)
  Step 4: 抓取球員名單與位置  → fetch_top5_leagues_top_players_sofascore.py
                               → top5_leagues_top_players_std.py
          (確保 position 欄位寫入 CSV，供陣型板使用)

用法（請從 backend/ 目錄執行）：
  python scripts/master_sync.py
  python scripts/master_sync.py --skip-standings   # 跳過積分榜更新
  python scripts/master_sync.py --skip-tactics     # 跳過陣型資料更新
  python scripts/master_sync.py --skip-ml          # 跳過 ML 回饋循環
  python scripts/master_sync.py --skip-players     # 跳過球員位置更新
  python scripts/master_sync.py --dry-run          # 預覽所有步驟，不實際執行
"""
import argparse
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

SCRIPTS_DIR = Path(_BACKEND) / "scripts"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def _banner(text: str) -> None:
    log.info("=" * 65)
    log.info("  %s", text)
    log.info("=" * 65)


def _run(script: str, extra_args: list | None = None, dry_run: bool = False) -> bool:
    """Run a script from the scripts/ directory, return True on success."""
    path = SCRIPTS_DIR / script
    cmd = [sys.executable, str(path)] + (extra_args or [])
    if dry_run:
        log.info("  [dry-run] 跳過: %s", " ".join(str(c) for c in cmd))
        return True
    log.info("  ▶  %s", " ".join(str(c) for c in cmd))
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(cmd, cwd=_BACKEND, env=env)
    if result.returncode != 0:
        log.error("  ❌ 腳本失敗 (exit %d): %s", result.returncode, script)
        return False
    log.info("  ✅ %s 完成", script)
    return True


def step1_standings(dry_run: bool) -> bool:
    _banner("Step 1  抓取最新聯賽積分榜")
    return _run("fetch_top5_standings.py", dry_run=dry_run)


def step2_tactics(dry_run: bool) -> bool:
    _banner("Step 2  抓取戰術陣型數據")
    return _run("ingest_tactical_data.py", dry_run=dry_run)


def step3_ml_pipeline(dry_run: bool) -> bool:
    _banner("Step 3  ML 回饋循環（賽果→重訓→更新預測）")
    return _run("update_results_and_retrain.py", dry_run=dry_run)


def step4_players(dry_run: bool) -> bool:
    _banner("Step 4  球員名單與位置同步")
    ok = _run("fetch_top5_leagues_top_players_sofascore.py", dry_run=dry_run)
    if ok:
        ok = _run("top5_leagues_top_players_std.py", dry_run=dry_run)
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(
        description="全自動數據同步：積分 → 陣型 → 賽果/重訓/預測 → 球員位置",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--skip-standings", action="store_true", help="跳過 Step 1 積分榜更新")
    parser.add_argument("--skip-tactics",   action="store_true", help="跳過 Step 2 陣型資料更新")
    parser.add_argument("--skip-ml",        action="store_true", help="跳過 Step 3 ML 回饋循環")
    parser.add_argument("--skip-players",   action="store_true", help="跳過 Step 4 球員位置更新")
    parser.add_argument("--dry-run",        action="store_true", help="預覽模式，不實際執行任何腳本")
    args = parser.parse_args()

    start = datetime.now()
    _banner("master_sync.py 啟動" + ("  [DRY-RUN]" if args.dry_run else ""))
    log.info("  時間: %s", start.strftime("%Y-%m-%d %H:%M:%S"))

    results: dict[str, bool | None] = {
        "1_standings": None,
        "2_tactics":   None,
        "3_ml":        None,
        "4_players":   None,
    }

    if args.skip_standings:
        log.info("\n⏭  跳過 Step 1 (--skip-standings)")
        results["1_standings"] = True
    else:
        results["1_standings"] = step1_standings(args.dry_run)

    if args.skip_tactics:
        log.info("\n⏭  跳過 Step 2 (--skip-tactics)")
        results["2_tactics"] = True
    else:
        results["2_tactics"] = step2_tactics(args.dry_run)

    if args.skip_ml:
        log.info("\n⏭  跳過 Step 3 (--skip-ml)")
        results["3_ml"] = True
    else:
        results["3_ml"] = step3_ml_pipeline(args.dry_run)

    if args.skip_players:
        log.info("\n⏭  跳過 Step 4 (--skip-players)")
        results["4_players"] = True
    else:
        results["4_players"] = step4_players(args.dry_run)

    elapsed = (datetime.now() - start).seconds
    _banner("執行摘要")
    labels = {
        "1_standings": "Step 1  抓取積分榜",
        "2_tactics":   "Step 2  抓取陣型資料",
        "3_ml":        "Step 3  ML 回饋循環",
        "4_players":   "Step 4  球員名單與位置",
    }
    all_ok = True
    for key, label in labels.items():
        ok = results[key]
        icon = "✅" if ok else ("⏭ " if ok is None else "❌")
        if ok is False:
            all_ok = False
        log.info("  %s  %s", icon, label)

    log.info("\n  總耗時: %ds", elapsed)
    if all_ok:
        log.info("🎉  全部完成！數據已同步，模型已更新。")
    else:
        log.error("⚠️  部分步驟失敗，請查看上方日誌。")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

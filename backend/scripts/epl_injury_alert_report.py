"""Cross-check EPL key players against the current injury list.

Reads the output files produced by:
  - fetch_epl_top_players_sofascore.py  →  epl_top_players_sofascore.csv
  - fetch_epl_injuries_sofascore.py     →  epl_injuries_sofascore.csv

Matches are performed by player_id (numeric Sofascore ID) so name-spelling
differences do not cause false negatives.

Usage:
    python epl_injury_alert_report.py

Output:
    epl_injury_alert_report.csv
    Columns: stat_type, rank, player_name, player_id, team,
             goals, assists, rating, injury_reason, position
"""

import csv
import sys
from pathlib import Path

TOP_PLAYERS_CSV = "epl_top_players_sofascore.csv"
INJURIES_CSV = "epl_injuries_sofascore.csv"
ALERT_REPORT_CSV = "epl_injury_alert_report.csv"


def load_csv(filepath):
    """Load a CSV file and return a list of row dicts."""
    rows = []
    with open(filepath, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def build_injury_lookup(injuries):
    """Return a dict keyed by player_id → injury record."""
    return {row["player_id"]: row for row in injuries if row.get("player_id")}


def generate_alerts(top_players, injury_lookup):
    """Return alert rows for key players found in the injury lookup."""
    alerts = []
    for player in top_players:
        pid = player.get("player_id", "")
        if pid and pid in injury_lookup:
            injury = injury_lookup[pid]
            alerts.append({
                "stat_type": player.get("stat_type", ""),
                "rank": player.get("rank", ""),
                "player_name": player.get("player_name", ""),
                "player_id": pid,
                "team": player.get("team", ""),
                "goals": player.get("goals", ""),
                "assists": player.get("assists", ""),
                "rating": player.get("rating", ""),
                "injury_reason": injury.get("injury_reason", ""),
                "position": injury.get("position", ""),
            })
    return alerts


def save_alert_report(alerts, filename=ALERT_REPORT_CSV):
    fieldnames = [
        "stat_type", "rank", "player_name", "player_id", "team",
        "goals", "assists", "rating", "injury_reason", "position",
    ]
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(alerts)
    print(f"✅ Saved alert report: {filename} ({len(alerts)} alerts)")


if __name__ == "__main__":
    for required in (TOP_PLAYERS_CSV, INJURIES_CSV):
        if not Path(required).exists():
            print(f"❌ Missing input file: {required}")
            print(f"   Run the corresponding fetch script first.")
            sys.exit(1)

    print(f"Loading {TOP_PLAYERS_CSV}...")
    top_players = load_csv(TOP_PLAYERS_CSV)
    print(f"  {len(top_players)} key player rows loaded")

    print(f"Loading {INJURIES_CSV}...")
    injuries = load_csv(INJURIES_CSV)
    print(f"  {len(injuries)} injured/doubtful players loaded")

    injury_lookup = build_injury_lookup(injuries)
    alerts = generate_alerts(top_players, injury_lookup)

    print(f"\n🚨 {len(alerts)} key player(s) currently injured/doubtful:")
    for alert in alerts:
        print(
            f"  [{alert['stat_type']}] #{alert['rank']} "
            f"{alert['player_name']} ({alert['team']}) "
            f"— {alert['injury_reason']}"
        )

    save_alert_report(alerts)

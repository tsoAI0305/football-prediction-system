import csv
from pathlib import Path
import unidecode

LEAGUES = [
    "epl",
    "laliga",
    "bundesliga",
    "serie_a",
    "ligue_1",
]

def norm_name(name):
    """轉小寫 + 去空白 + 去 accent（重音）"""
    return unidecode.unidecode(name or "").lower().strip()

def load_csv(filepath):
    rows = []
    with open(filepath, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def build_injury_lookup(injuries):
    # norm player_name + team_std, join可靠
    lookup_by_pid = {row.get("player_id", ""): row for row in injuries if row.get("player_id", "")}
    # 還支援沒 player_id 的情況
    lookup_by_name_team = {}
    for row in injuries:
        key = (norm_name(row.get("player", "")), row.get("team_std", "").lower().strip())
        lookup_by_name_team[key] = row
    return lookup_by_pid, lookup_by_name_team

def generate_alerts(top_players, injury_lookup_by_pid, injury_lookup_by_name_team):
    alerts = []
    for player in top_players:
        pid = player.get("player_id", "")
        found = None

        if pid and pid in injury_lookup_by_pid:
            found = injury_lookup_by_pid[pid]
        else:
            key = (norm_name(player.get("player_name", "")), player.get("team_std","").lower().strip())
            found = injury_lookup_by_name_team.get(key, None)
        if found:
            alerts.append({
                "stat_type": player.get("stat_type", ""),
                "rank": player.get("rank", ""),
                "player_name": player.get("player_name", ""),
                "player_id": pid,
                "team": player.get("team_std", player.get("team", "")),
                "goals": player.get("goals", ""),
                "assists": player.get("assists", ""),
                "rating": player.get("rating", ""),
                "injury_reason": found.get("info", ""),
                "position": found.get("position", ""),
            })
    return alerts

def dedup_merge_alerts(alerts):
    from collections import defaultdict
    grouped = defaultdict(list)
    for a in alerts:
        pid = str(a.get("player_id", "")).strip()
        grouped[pid].append(a)
    merged = []
    for pid, acts in grouped.items():
        types_and_ranks = [
            (a["stat_type"], a.get("rank", "")) for a in acts if a.get("stat_type")
        ]
        types_and_ranks.sort()
        stat_types = "|".join(t for t, _ in types_and_ranks)
        ranks = "|".join(r for _, r in types_and_ranks)
        base = acts[0].copy()
        base["stat_types"] = stat_types
        base["rank"] = ranks
        merged.append(base)
    return merged

def save_alert_report(alerts, filename):
    fieldnames = [
        "player_name", "player_id", "team", "stat_types", "rank",
        "goals", "assists", "rating", "injury_reason", "position"
    ]
    filtered_alerts = [
        {k: alert.get(k, "") for k in fieldnames} for alert in alerts
    ]
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered_alerts)
    print(f"✅ Saved alert report: {filename} ({len(alerts)} alerts)")

if __name__ == "__main__":
    for league in LEAGUES:
        DATA_DIR = Path(__file__).resolve().parents[1] / "data"
        top_players_csv = DATA_DIR / f"{league}_team_top_players_sofascore_std.csv"
        injuries_csv = DATA_DIR / f"{league}_teams_injuries_sportsgambler.csv"
        alert_csv = DATA_DIR / f"{league}_injury_alert_report.csv"

        if not top_players_csv.exists() or not injuries_csv.exists():
            print(f"❌ Missing file for {league}; skip.")
            continue

        print(f"\n== {league.upper()} ==")
        top_players = load_csv(top_players_csv)
        injuries = load_csv(injuries_csv)
        inj_pid, inj_name_team = build_injury_lookup(injuries)
        alerts = generate_alerts(top_players, inj_pid, inj_name_team)
        merged_alerts = dedup_merge_alerts(alerts)
        save_alert_report(merged_alerts, alert_csv)
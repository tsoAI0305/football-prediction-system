import json
import pandas as pd
from pathlib import Path

data_dir = Path(__file__).resolve().parents[1] / "data"

_map_file = data_dir / "team_name_map.json"
if _map_file.exists():
    with open(_map_file, "r", encoding="utf-8") as f:
        team_name_map = json.load(f)
else:
    team_name_map = {}

def map_team_name(team_name):
    return team_name_map.get(team_name, team_name)

for csv_file in data_dir.glob("*_team_top_players_sofascore.csv"):
    std_csv = csv_file.with_name(csv_file.stem + "_std.csv")
    df = pd.read_csv(csv_file)
    df["team_std"] = df["team"].map(map_team_name)
    df.to_csv(std_csv, index=False)
    print(f"✅ std轉換完成: {std_csv}")
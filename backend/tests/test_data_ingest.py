import json
import pandas as pd
import pytest
from app.services import data_ingest as di


def test_read_csv_and_match_id(tmp_path):
    p = tmp_path / "fixtures.csv"
    df = pd.DataFrame({"date":["2026-01-01"], "home_team":["A"]})
    df.to_csv(p, index=False)
    out = di.load_fixtures(str(p))
    assert "match_id" in out.columns
    assert pd.api.types.is_datetime64_any_dtype(out["date"]) 


def test_read_ndjson(tmp_path):
    p = tmp_path / "players.ndjson"
    lines = [json.dumps({"player_id":"p1","team":"A"}), json.dumps({"player_id":"p2","team":"B"})]
    p.write_text("\n".join(lines), encoding="utf-8")
    out = di._read_any(str(p))
    assert len(out) == 2
    assert "player_id" in out.columns


def test_validate_schema_and_nulls():
    df = pd.DataFrame({"a":[1,None], "b":[None,None]})
    ok, errors = di.validate_schema(df, {"a":"int","b":"int"}, null_threshold=0.5)
    assert not ok
    assert any("high null rate" in e for e in errors)


def test_normalize_team_names():
    df = pd.DataFrame({"team":["Alpha","Beta"]})
    mapping = {"Alpha":"ALP"}
    out = di.normalize_team_names(df, mapping, team_col="team")
    assert out.loc[0,"team_std"] == "ALP"
    assert out.loc[1,"team_std"] == "Beta"

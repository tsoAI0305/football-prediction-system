# minimal pytest test for validate_schema
import pandas as pd
from app.services.data_ingest import validate_schema

def test_validate_schema_missing_col():
    df = pd.DataFrame({"a":[1,2,3]})
    ok, errs = validate_schema(df, {"match_id":"str", "date":"datetime"})
    assert not ok
    assert any("missing column" in e for e in errs)
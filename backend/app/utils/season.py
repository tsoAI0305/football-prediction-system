"""Football season codes like 2122 (Aug 2021 – May 2022)."""
from datetime import datetime


def season_from_date(dt: datetime | None) -> str | None:
    """Map a match date to football-data.co.uk season code (e.g. 2526)."""
    if dt is None:
        return None
    year = dt.year
    if dt.month >= 8:
        start, end = year, year + 1
    else:
        start, end = year - 1, year
    return f"{start % 100:02d}{end % 100:02d}"

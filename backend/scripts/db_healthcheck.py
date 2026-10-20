"""Check Postgres connectivity using DATABASE_URL or local Docker defaults."""
import os
import sys

import psycopg2

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://football_user:football_pass@localhost:5432/football_db",
)

try:
    conn = psycopg2.connect(DATABASE_URL)
    print("PostgreSQL 連線成功")
    conn.close()
except Exception as e:
    print(f"連線失敗：{e}", file=sys.stderr)
    sys.exit(1)

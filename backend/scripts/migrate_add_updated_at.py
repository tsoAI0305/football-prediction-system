"""
scripts/migrate_add_updated_at.py

One-shot migration: add missing updated_at column to predictions table.
Safe to run multiple times (uses ADD COLUMN IF NOT EXISTS).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import SessionLocal

def main():
    db = SessionLocal()
    try:
        # 1. Add column if missing
        db.execute(text("""
            ALTER TABLE predictions
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE
                DEFAULT CURRENT_TIMESTAMP
        """))

        # 2. Backfill existing rows: set updated_at = created_at where still NULL
        db.execute(text("""
            UPDATE predictions
            SET updated_at = created_at
            WHERE updated_at IS NULL AND created_at IS NOT NULL
        """))

        db.commit()

        # 3. Verify
        row = db.execute(text(
            "SELECT COUNT(*) FROM predictions WHERE updated_at IS NULL"
        )).scalar()
        total = db.execute(text("SELECT COUNT(*) FROM predictions")).scalar()
        print(f"✅ Migration done — predictions: {total} rows, still-null updated_at: {row}")

    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()

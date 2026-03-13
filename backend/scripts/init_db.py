"""Initialize database with updated schema."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from app.models.match import Match
from app.models.team import Team
from app.models.prediction import Prediction
# 匯入其他所有模型...

def init_db():
    """Create all tables."""
    print("🗄️  Creating database tables...")
    
    # 這會根據模型建立所有表格
    # 如果表格已存在，會自動加入新欄位（在大部分情況下）
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database tables created successfully!")

if __name__ == "__main__":
    init_db()
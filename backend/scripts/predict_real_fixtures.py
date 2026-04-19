"""預測真實賽程並加入 AI 深度分析"""
import json
import os
import sys
import logging
from app.services.logging_config import configure_logging

# Ensure centralized logging configured
configure_logging()
logger = logging.getLogger(__name__)

sys.path.insert(0, 'scripts')

from predict_match import predict_match

# 嘗試載入 AI 模組
try:
    from predict_with_ai import predict_match_with_ai
    HAS_AI = True
    logger.info("✅ AI 分析模組已載入")
except ImportError as e:
    logger.warning(f"⚠️  無法載入 AI 模組: {e}")
    HAS_AI = False

def load_fixtures():
    """載入賽程資料"""
    with open('data/real_fixtures.json', 'r', encoding='utf-8') as f:
        fixtures = json.load(f)
    logger.info(f"✅ 載入 {len(fixtures)} 場賽程\n")
    return fixtures

def predict_all_fixtures():
    """預測所有賽程並加入 AI 分析"""
    fixtures = load_fixtures()
    predictions = []
    total = len(fixtures)
    ai_count = 0
    
    logger.info(f"🤖 開始預測 {total} 場比賽（包含 AI 分析）...\n")
    
    for idx, fixture in enumerate(fixtures, 1):
        home_team = fixture['home_team']
        away_team = fixture['away_team']
        
        logger.info(f"[{idx}/{total}] {home_team} vs {away_team}")
        
        try:
            # 取得基礎預測
            basic_pred = predict_match(home_team, away_team)
            
            if "error" in basic_pred:
                logger.warning(f"  ⚠️  跳過")
                continue
            
            ai_analysis = None
            
            # 如果有 AI 模組，生成分析
            if HAS_AI:
                logger.info(f"  🤖 生成 AI 分析...")
                try:
                    ai_result = predict_match_with_ai(home_team, away_team)
                    if "ai_analysis" in ai_result:
                        ai_analysis = ai_result["ai_analysis"]
                        if ai_analysis:
                            ai_count += 1
                            print(f"  ✅ 完成 ({len(ai_analysis)} 字元)")
                        else:
                            print(f"  ⚠️  AI 返回空")
                except Exception as e:
                    logger.exception(f"  ⚠️  AI 錯誤: {e}")
            
            # 組合結果
            predictions.append({
                "date": fixture["date"],
                "time": fixture["time"],
                "league": fixture["league"],
                "home_team": home_team,
                "away_team": away_team,
                "prediction": basic_pred,
                "ai_analysis": ai_analysis
            })
            
        except Exception as e:
            logger.exception(f"  ❌ 錯誤: {e}")
    
    # 儲存
    with open('data/final_predictions.json', 'w', encoding='utf-8') as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n✅ 完成！成功: {len(predictions)}/{total}, AI: {ai_count}/{len(predictions)}")

if __name__ == "__main__":
    predict_all_fixtures()

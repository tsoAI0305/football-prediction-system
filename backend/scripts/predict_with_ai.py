"""AI-enhanced prediction using Groq."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from groq import Groq
from scripts.predict_match import predict_match

def get_ai_analysis(home_team, away_team, basic_prediction):
    """
    使用 Groq AI 深度分析比賽
    
    模型: llama-3.3-70b-versatile (快速且準確)
    """
    
    # 初始化 Groq 客戶端
    api_key = os.getenv('GROQ_API_KEY')
    
    if not api_key:
        return {
            'ai_analysis': '⚠️ 未設定 GROQ_API_KEY，無法使用 AI 分析',
            'ai_available': False,
        }
    
    client = Groq(api_key=api_key)
    analysis = basic_prediction['analysis']
    
    prompt = f"""你是專業足球分析師。請分析以下比賽並給出深度見解。

⚽ 比賽: {home_team} (主場) vs {away_team} (客場)

📊 數據分析:
主隊 {home_team}:
- 近期狀態: {analysis['home_form']} (狀態分: {analysis['home_form_score']})
- 主場勝率: {analysis['home_win_rate']}%
- 場均進球: {analysis['home_avg_goals']}
- 綜合實力: {analysis['home_total_score']}/100

客隊 {away_team}:
- 近期狀態: {analysis['away_form']} (狀態分: {analysis['away_form_score']})
- 客場勝率: {analysis['away_win_rate']}%
- 場均進球: {analysis['away_avg_goals']}
- 綜合實力: {analysis['away_total_score']}/100

🎯 基礎預測:
- 結果: {basic_prediction['prediction']} ({
    '主場獲勝' if basic_prediction['prediction'] == 'home_win' 
    else '客場獲勝' if basic_prediction['prediction'] == 'away_win' 
    else '平局'
})
- 信心度: {basic_prediction['confidence']}%
- 預測比分: {basic_prediction['expected_score']}
- 機率分布: 主勝 {basic_prediction['probabilities']['home_win']}% | 和局 {basic_prediction['probabilities']['draw']}% | 客勝 {basic_prediction['probabilities']['away_win']}%

請提供以下分析（用繁體中文，簡潔專業）:

1. 📋 關鍵因素 (列出3個最重要的影響因素，每點20-30字)

2. ⚠️ 風險提示 (指出1-2個可能影響預測準確度的因素)

3. 💡 AI 建議:
   - 是否同意基礎預測結果？
   - 信心度是否合理？(過高/過低/合理)
   - 如果不同意，你的預測是什麼？

4. 🎯 調整建議:
   - 預測比分是否需要調整？如需要請給出你的比分
   - 最終信心度應該是多少？

請直接給出分析，不需要重複問題。每個段落用明確的標題區分。"""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "你是專業的足球數據分析師，擅長根據數據給出精準的比賽預測分析。回答請使用繁體中文，簡潔專業。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",  # Groq 最強模型
            temperature=0.7,
            max_tokens=1000,
        )
        
        ai_insight = chat_completion.choices[0].message.content
        
        return {
            'ai_analysis': ai_insight,
            'ai_available': True,
            'ai_model': 'Groq Llama 3.3 70B',
        }
        
    except Exception as e:
        return {
            'ai_analysis': f'⚠️ AI 分析錯誤: {str(e)}',
            'ai_available': False,
        }

def predict_match_with_ai(home_team, away_team):
    """整合 AI 的完整預測."""
    
    print(f"🔍 分析比賽: {home_team} vs {away_team}")
    print("📊 執行基礎數據分析...")
    
    # 1. 基礎預測
    basic_result = predict_match(home_team, away_team)
    
    if 'error' in basic_result:
        return basic_result
    
    print("🤖 啟動 AI 深度分析...")
    
    # 2. AI 增強分析
    ai_result = get_ai_analysis(home_team, away_team, basic_result)
    
    # 3. 合併結果
    return {
        **basic_result,
        **ai_result,
    }

if __name__ == "__main__":
    print("="*70)
    print("🤖 AI 增強足球預測系統 (Powered by Groq)")
    print("="*70)
    
    # 測試重點比賽
    tests = [
        ('Barcelona', 'Sevilla'),
        ('Manchester City', 'West Ham'),
        ('Bayern Munich', 'Leverkusen'),
    ]
    
    for home, away in tests:
        print(f"\n{'='*70}")
        print(f"⚽ {home} (主場) vs {away} (客場)")
        print('='*70)
        
        result = predict_match_with_ai(home, away)
        
        if 'error' not in result:
            print(f"\n📊 基礎數據預測:")
            print(f"{'─'*70}")
            
            pred_text = {
                'home_win': f'🏠 {home} 主場獲勝',
                'away_win': f'✈️ {away} 客場獲勝',
                'draw': '🤝 平局'
            }
            
            print(f"   結果: {pred_text[result['prediction']]}")
            print(f"   信心度: {result['confidence']}%")
            print(f"   預測比分: {result['expected_score']}")
            print(f"   機率分布: 主勝 {result['probabilities']['home_win']}% | "
                  f"和局 {result['probabilities']['draw']}% | "
                  f"客勝 {result['probabilities']['away_win']}%")
            
            print(f"\n   主隊實力: {result['analysis']['home_total_score']}/100")
            print(f"   ├─ 近況: {result['analysis']['home_form']} ({result['analysis']['home_form_score']}分)")
            print(f"   ├─ 勝率: {result['analysis']['home_win_rate']}%")
            print(f"   └─ 場均: {result['analysis']['home_avg_goals']}球")
            
            print(f"\n   客隊實力: {result['analysis']['away_total_score']}/100")
            print(f"   ├─ 近況: {result['analysis']['away_form']} ({result['analysis']['away_form_score']}分)")
            print(f"   ├─ 勝率: {result['analysis']['away_win_rate']}%")
            print(f"   └─ 場均: {result['analysis']['away_avg_goals']}球")
            
            if result.get('ai_available'):
                print(f"\n🤖 AI 深度分析 ({result.get('ai_model', 'Unknown')}):")
                print(f"{'─'*70}")
                print(result['ai_analysis'])
            else:
                print(f"\n{result['ai_analysis']}")
        else:
            print(f"❌ 錯誤: {result['error']}")
        
        print(f"\n{'='*70}\n")

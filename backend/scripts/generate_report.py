"""Generate comprehensive HTML prediction report."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime

predictions_file = "data/final_predictions.json"

if not os.path.exists(predictions_file):
    print(f"❌ 找不到預測檔案: {predictions_file}")
    print("請先執行: docker compose exec api python scripts/predict_real_fixtures.py")
    exit(1)

with open(predictions_file, "r", encoding="utf-8") as f:
    predictions = json.load(f)

print(f"📄 生成 HTML 報告 ({len(predictions)} 場比賽)")

# 按日期和聯賽分組
by_date_league = {}
for p in predictions:
    date = p['date']
    league = p['league']
    key = f"{date}|{league}"
    
    if key not in by_date_league:
        by_date_league[key] = []
    by_date_league[key].append(p)

html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚽ 足球預測系統 - 2026/03/14-17 賽事預測</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: "Segoe UI", "Microsoft JhengHei", Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{ 
            max-width: 1400px; 
            margin: 0 auto; 
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{ 
            text-align: center; 
            color: #333;
            margin-bottom: 10px;
            font-size: 2.8em;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 40px;
            font-size: 1.2em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
            background: #f8f9fa;
            padding: 30px;
            border-radius: 15px;
        }}
        .stat-box {{
            text-align: center;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stat-label {{
            color: #666;
            margin-top: 10px;
            font-size: 0.95em;
        }}
        
        .date-separator {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 15px 25px;
            margin: 40px 0 20px 0;
            border-radius: 10px;
            font-size: 1.4em;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .league-header {{
            background: #764ba2;
            color: white;
            padding: 12px 20px;
            margin: 25px 0 15px 0;
            border-radius: 8px;
            font-size: 1.2em;
            font-weight: 600;
        }}
        
        .match {{
            border: 2px solid #e0e0e0;
            margin: 15px 0;
            padding: 25px;
            border-radius: 15px;
            transition: all 0.3s;
            background: white;
        }}
        .match:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            border-color: #667eea;
        }}
        
        .match-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        .match-time {{
            background: #667eea;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
        }}
        
        .teams {{
            text-align: center;
            font-size: 1.5em;
            font-weight: bold;
            margin: 20px 0;
            color: #333;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
        }}
        .team-name {{
            flex: 1;
            max-width: 200px;
        }}
        .vs {{
            color: #667eea;
            font-size: 0.7em;
        }}
        
        .prediction {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 12px;
            margin: 20px 0;
        }}
        .prediction-result {{
            font-size: 1.8em;
            font-weight: bold;
            margin-bottom: 10px;
            text-align: center;
        }}
        .confidence {{
            font-size: 1.2em;
            text-align: center;
            margin-bottom: 15px;
        }}
        
        .probabilities {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
        }}
        .prob-box {{
            text-align: center;
        }}
        .prob-value {{
            font-size: 2em;
            font-weight: bold;
        }}
        .prob-label {{
            font-size: 0.9em;
            margin-top: 5px;
        }}
        
        .score {{
            font-size: 2.5em;
            font-weight: bold;
            text-align: center;
            color: #667eea;
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }}
        
        .analysis {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
        }}
        .team-analysis {{
            padding: 15px;
            background: white;
            border-radius: 10px;
        }}
        .team-analysis h4 {{
            color: #667eea;
            margin-bottom: 12px;
            font-size: 1.1em;
        }}
        .stat-row {{
            margin: 10px 0;
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
        }}
        .stat-row:last-child {{
            border-bottom: none;
        }}
        .stat-value {{
            color: #667eea;
            font-weight: 600;
        }}
        .form {{
            font-family: "Courier New", monospace;
            font-size: 1.1em;
            letter-spacing: 2px;
            font-weight: bold;
        }}
        
        .home-win {{ border-left: 5px solid #4caf50; }}
        .away-win {{ border-left: 5px solid #f44336; }}
        .draw {{ border-left: 5px solid #ff9800; }}
        
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding: 30px;
            border-top: 2px solid #e0e0e0;
            color: #666;
        }}
        .footer-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .footer-stat {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
        }}
        
        @media (max-width: 768px) {{
            .analysis {{ grid-template-columns: 1fr; }}
            .teams {{ font-size: 1.2em; }}
            h1 {{ font-size: 2em; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚽ AI 足球預測系統</h1>
        <div class="subtitle">2026年3月14-17日 賽事預測報告</div>
        
        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-number">{len(predictions)}</div>
                <div class="stat-label">預測場次</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">5</div>
                <div class="stat-label">歐洲聯賽</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">AI</div>
                <div class="stat-label">深度分析</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">96</div>
                <div class="stat-label">球隊數據</div>
            </div>
        </div>
"""

total_home_win = sum(1 for p in predictions if p['prediction']['prediction'] == 'home_win')
total_draw = sum(1 for p in predictions if p['prediction']['prediction'] == 'draw')
total_away_win = sum(1 for p in predictions if p['prediction']['prediction'] == 'away_win')

sorted_keys = sorted(by_date_league.keys())

for key in sorted_keys:
    date, league = key.split('|')
    matches = by_date_league[key]
    
    if key == sorted_keys[0] or date != sorted_keys[sorted_keys.index(key)-1].split('|')[0]:
        date_matches = len([m for k, ms in by_date_league.items() if k.startswith(date) for m in ms])
        html += f'<div class="date-separator"><span>📅 {date}</span><span>{date_matches} 場比賽</span></div>'
    
    html += f'<div class="league-header">🏆 {league}</div>'
    
    for p in matches:
        pred = p['prediction']
        analysis = pred['analysis']
        border_class = pred['prediction'].replace('_', '-')
        
        result_emoji = {'home_win': '🏠', 'away_win': '✈️', 'draw': '🤝'}
        result_text = {
            'home_win': f"{p['home_team']} 主場獲勝",
            'away_win': f"{p['away_team']} 客場獲勝",
            'draw': '平局'
        }
        
        html += f"""
        <div class="match {border_class}">
            <div class="match-header">
                <span class="match-time">⏰ {p['time']}</span>
            </div>
            
            <div class="teams">
                <div class="team-name">{p['home_team']}</div>
                <span class="vs">vs</span>
                <div class="team-name">{p['away_team']}</div>
            </div>
            
            <div class="prediction">
                <div class="prediction-result">
                    {result_emoji[pred['prediction']]} {result_text[pred['prediction']]}
                </div>
                <div class="confidence">信心度: {pred['confidence']}%</div>
                
                <div class="probabilities">
                    <div class="prob-box">
                        <div class="prob-value">{pred['probabilities']['home_win']}%</div>
                        <div class="prob-label">🏠 主勝</div>
                    </div>
                    <div class="prob-box">
                        <div class="prob-value">{pred['probabilities']['draw']}%</div>
                        <div class="prob-label">🤝 和局</div>
                    </div>
                    <div class="prob-box">
                        <div class="prob-value">{pred['probabilities']['away_win']}%</div>
                        <div class="prob-label">✈️ 客勝</div>
                    </div>
                </div>
            </div>
            
            <div class="score">預測比分: {pred['expected_score']}</div>
            
            <div class="analysis">
                <div class="team-analysis">
                    <h4>🏠 {p['home_team']}</h4>
                    <div class="stat-row">
                        <strong>近期狀態:</strong>
                        <span class="form stat-value">{analysis['home_form']}</span>
                    </div>
                    <div class="stat-row">
                        <strong>綜合實力:</strong>
                        <span class="stat-value">{analysis['home_total_score']}/100</span>
                    </div>
                    <div class="stat-row">
                        <strong>主場勝率:</strong>
                        <span class="stat-value">{analysis['home_win_rate']}%</span>
                    </div>
                    <div class="stat-row">
                        <strong>場均進球:</strong>
                        <span class="stat-value">{analysis['home_avg_goals']}</span>
                    </div>
                </div>
                
                <div class="team-analysis">
                    <h4>✈️ {p['away_team']}</h4>
                    <div class="stat-row">
                        <strong>近期狀態:</strong>
                        <span class="form stat-value">{analysis['away_form']}</span>
                    </div>
                    <div class="stat-row">
                        <strong>綜合實力:</strong>
                        <span class="stat-value">{analysis['away_total_score']}/100</span>
                    </div>
                    <div class="stat-row">
                        <strong>客場勝率:</strong>
                        <span class="stat-value">{analysis['away_win_rate']}%</span>
                    </div>
                    <div class="stat-row">
                        <strong>場均進球:</strong>
                        <span class="stat-value">{analysis['away_avg_goals']}</span>
                    </div>
                </div>
            </div>
        </div>
"""

html += f"""
        <div class="footer">
            <h3>📊 預測統計摘要</h3>
            <div class="footer-stats">
                <div class="footer-stat">
                    <strong>🏠 主場獲勝</strong><br>
                    {total_home_win} 場 ({total_home_win/len(predictions)*100:.1f}%)
                </div>
                <div class="footer-stat">
                    <strong>🤝 平局</strong><br>
                    {total_draw} 場 ({total_draw/len(predictions)*100:.1f}%)
                </div>
                <div class="footer-stat">
                    <strong>✈️ 客場獲勝</strong><br>
                    {total_away_win} 場 ({total_away_win/len(predictions)*100:.1f}%)
                </div>
            </div>
            
            <h3 style="margin-top: 30px;">⚙️ 預測系統說明</h3>
            <div class="footer-stats">
                <div class="footer-stat">
                    <strong>📊 數據來源</strong><br>
                    2025/26 賽季官方比賽資料
                </div>
                <div class="footer-stat">
                    <strong>🤖 AI 模型</strong><br>
                    Groq Llama 3.3 70B
                </div>
                <div class="footer-stat">
                    <strong>📈 分析維度</strong><br>
                    近況+勝率+進攻+防守
                </div>
                <div class="footer-stat">
                    <strong>🏆 涵蓋聯賽</strong><br>
                    英超、西甲、德甲、意甲、法甲
                </div>
            </div>
            
            <p style="margin-top: 30px; color: #999; font-size: 0.95em;">
                生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
                預測僅供參考，實際結果可能不同
            </p>
        </div>
    </div>
</body>
</html>
"""

output_file = "data/prediction_report.html"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ HTML 報告已生成")
print(f"📁 檔案位置: {output_file}")
print(f"\n📊 預測分布:")
print(f"   🏠 主場獲勝: {total_home_win} 場 ({total_home_win/len(predictions)*100:.1f}%)")
print(f"   🤝 平局: {total_draw} 場 ({total_draw/len(predictions)*100:.1f}%)")
print(f"   ✈️ 客場獲勝: {total_away_win} 場 ({total_away_win/len(predictions)*100:.1f}%)")

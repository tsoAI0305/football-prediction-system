"""Calculate team statistics for CURRENT SEASON ONLY."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime
from collections import defaultdict
from app.database import SessionLocal
from app.models.match import Match

def calculate_current_season_stats():
    """只計算當前賽季 (2025/26) 的統計."""
    
    db = SessionLocal()
    
    # 當前賽季起始日期：2025年8月1日
    season_start = datetime(2025, 8, 1)
    
    matches = db.query(Match).filter(
        Match.match_date >= season_start,
        Match.status == 'finished'
    ).all()
    
    print(f"📊 分析 2025/26 賽季比賽")
    print(f"   起始日期: {season_start.date()}")
    print(f"   總比賽數: {len(matches)}\n")
    
    team_stats = defaultdict(lambda: {
        'total_matches': 0,
        'home_matches': 0,
        'away_matches': 0,
        'wins': 0,
        'draws': 0,
        'losses': 0,
        'home_wins': 0,
        'home_draws': 0,
        'home_losses': 0,
        'away_wins': 0,
        'away_draws': 0,
        'away_losses': 0,
        'goals_scored': 0,
        'goals_conceded': 0,
        'goals_scored_home': 0,
        'goals_conceded_home': 0,
        'goals_scored_away': 0,
        'goals_conceded_away': 0,
        'recent_matches': [],
    })
    
    for match in matches:
        if match.home_score is None or match.away_score is None:
            continue
        
        home = match.home_team
        away = match.away_team
        
        # 主隊統計
        team_stats[home]['total_matches'] += 1
        team_stats[home]['home_matches'] += 1
        team_stats[home]['goals_scored'] += match.home_score
        team_stats[home]['goals_conceded'] += match.away_score
        team_stats[home]['goals_scored_home'] += match.home_score
        team_stats[home]['goals_conceded_home'] += match.away_score
        
        # 客隊統計
        team_stats[away]['total_matches'] += 1
        team_stats[away]['away_matches'] += 1
        team_stats[away]['goals_scored'] += match.away_score
        team_stats[away]['goals_conceded'] += match.home_score
        team_stats[away]['goals_scored_away'] += match.away_score
        team_stats[away]['goals_conceded_away'] += match.home_score
        
        # 勝負統計
        if match.home_score > match.away_score:
            team_stats[home]['wins'] += 1
            team_stats[home]['home_wins'] += 1
            team_stats[away]['losses'] += 1
            team_stats[away]['away_losses'] += 1
            home_result = 'W'
            away_result = 'L'
        elif match.home_score < match.away_score:
            team_stats[home]['losses'] += 1
            team_stats[home]['home_losses'] += 1
            team_stats[away]['wins'] += 1
            team_stats[away]['away_wins'] += 1
            home_result = 'L'
            away_result = 'W'
        else:
            team_stats[home]['draws'] += 1
            team_stats[home]['home_draws'] += 1
            team_stats[away]['draws'] += 1
            team_stats[away]['away_draws'] += 1
            home_result = 'D'
            away_result = 'D'
        
        # 記錄最近比賽
        team_stats[home]['recent_matches'].append({
            'date': match.match_date.isoformat(),
            'result': home_result,
            'opponent': away,
            'home': True,
        })
        team_stats[away]['recent_matches'].append({
            'date': match.match_date.isoformat(),
            'result': away_result,
            'opponent': home,
            'home': False,
        })
    
    # 計算衍生指標
    final_stats = {}
    for team, stats in team_stats.items():
        if stats['total_matches'] == 0:
            continue
        
        # 排序最近比賽
        stats['recent_matches'].sort(key=lambda x: x['date'], reverse=True)
        recent_5 = stats['recent_matches'][:5]
        recent_form = ''.join([m['result'] for m in recent_5])
        
        # 計算積分 (W=3, D=1, L=0)
        points = stats['wins'] * 3 + stats['draws'] * 1
        
        final_stats[team] = {
            # 基本數據
            'total_matches': stats['total_matches'],
            'wins': stats['wins'],
            'draws': stats['draws'],
            'losses': stats['losses'],
            'points': points,
            
            # 主場數據
            'home_matches': stats['home_matches'],
            'home_wins': stats['home_wins'],
            'home_draws': stats['home_draws'],
            'home_losses': stats['home_losses'],
            
            # 客場數據
            'away_matches': stats['away_matches'],
            'away_wins': stats['away_wins'],
            'away_draws': stats['away_draws'],
            'away_losses': stats['away_losses'],
            
            # 進球數據
            'goals_scored': stats['goals_scored'],
            'goals_conceded': stats['goals_conceded'],
            'goal_difference': stats['goals_scored'] - stats['goals_conceded'],
            'goals_scored_home': stats['goals_scored_home'],
            'goals_conceded_home': stats['goals_conceded_home'],
            'goals_scored_away': stats['goals_scored_away'],
            'goals_conceded_away': stats['goals_conceded_away'],
            
            # 平均數據
            'avg_goals_scored': round(stats['goals_scored'] / stats['total_matches'], 2),
            'avg_goals_conceded': round(stats['goals_conceded'] / stats['total_matches'], 2),
            'avg_goals_scored_home': round(stats['goals_scored_home'] / max(1, stats['home_matches']), 2),
            'avg_goals_conceded_home': round(stats['goals_conceded_home'] / max(1, stats['home_matches']), 2),
            'avg_goals_scored_away': round(stats['goals_scored_away'] / max(1, stats['away_matches']), 2),
            'avg_goals_conceded_away': round(stats['goals_conceded_away'] / max(1, stats['away_matches']), 2),
            
            # 勝率
            'win_rate': round(stats['wins'] / stats['total_matches'], 3),
            'home_win_rate': round(stats['home_wins'] / max(1, stats['home_matches']), 3),
            'away_win_rate': round(stats['away_wins'] / max(1, stats['away_matches']), 3),
            
            # 近期狀態
            'recent_form': recent_form,
        }
    
    # 儲存
    os.makedirs('data', exist_ok=True)
    with open('data/team_stats.json', 'w', encoding='utf-8') as f:
        json.dump(final_stats, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 計算完成！共 {len(final_stats)} 支球隊")
    print(f"📁 已儲存到 data/team_stats.json\n")
    
    # 顯示範例
    print("="*70)
    print("📊 主要球隊統計 (2025/26 賽季)")
    print("="*70)
    
    sample_teams = ['Barcelona', 'Real Madrid', 'Manchester City', 'Liverpool', 'Bayern Munich', 'Arsenal']
    for team in sample_teams:
        if team in final_stats:
            s = final_stats[team]
            print(f"\n⚽ {team}")
            print(f"   場次: {s['total_matches']} | 勝/平/敗: {s['wins']}/{s['draws']}/{s['losses']}")
            print(f"   積分: {s['points']} | 進球: {s['goals_scored']} | 失球: {s['goals_conceded']} | 淨勝球: {s['goal_difference']:+d}")
            print(f"   主場: {s['home_wins']}W {s['home_draws']}D {s['home_losses']}L | 客場: {s['away_wins']}W {s['away_draws']}D {s['away_losses']}L")
            print(f"   近5場: {s['recent_form']}")
    
    print("\n" + "="*70)
    
    db.close()
    return final_stats

if __name__ == "__main__":
    print("🚀 計算 2025/26 賽季球隊統計")
    print("="*70)
    calculate_current_season_stats()
    print("\n✅ 完成")

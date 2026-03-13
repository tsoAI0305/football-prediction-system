"""Fixed score prediction logic."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json

TEAM_NAME_MAPPING = {
    'Man City': 'Manchester City',
    'Man United': 'Manchester United',
    'Man Utd': 'Manchester United',
    'AC Milan': 'Milan',
    'AS Roma': 'Roma',
    'Paris Saint Germain': 'Paris SG',
    'PSG': 'Paris SG',
    'Stade Brestois 29': 'Brest',
    'Ath Madrid': 'Atletico Madrid',
    'Ath Bilbao': 'Athletic Bilbao',
}

def normalize_team_name(name):
    return TEAM_NAME_MAPPING.get(name, name)

def calculate_form_score(form_string):
    if not form_string:
        return 50
    
    score = 0
    weights = [5, 4, 3, 2, 1]
    
    for i, result in enumerate(form_string[:5]):
        weight = weights[i] if i < len(weights) else 1
        if result == 'W':
            score += 20 * weight
        elif result == 'D':
            score += 10 * weight
    
    max_score = sum([20 * w for w in weights[:len(form_string)]])
    return round((score / max_score * 100) if max_score > 0 else 50, 1)

def calculate_team_strength(team_stats, is_home=True):
    form_score = calculate_form_score(team_stats.get('recent_form', ''))
    
    if is_home:
        win_rate = team_stats.get('home_win_rate', 0) * 100
        avg_goals_scored = team_stats.get('avg_goals_scored_home', 0)
        avg_goals_conceded = team_stats.get('avg_goals_conceded_home', 0)
    else:
        win_rate = team_stats.get('away_win_rate', 0) * 100
        avg_goals_scored = team_stats.get('avg_goals_scored_away', 0)
        avg_goals_conceded = team_stats.get('avg_goals_conceded_away', 0)
    
    attack_score = min(avg_goals_scored / 3.0 * 100, 100)
    defense_score = max(0, (1 - avg_goals_conceded / 3.0) * 100)
    
    total_score = (
        form_score * 0.30 +
        win_rate * 0.30 +
        attack_score * 0.20 +
        defense_score * 0.20
    )
    
    return {
        'total': round(total_score, 1),
        'form': round(form_score, 1),
        'win_rate': round(win_rate, 1),
        'attack': round(attack_score, 1),
        'defense': round(defense_score, 1),
        'avg_goals_scored': round(avg_goals_scored, 2),
        'avg_goals_conceded': round(avg_goals_conceded, 2),
    }

def predict_score_improved(home_strength, away_strength, confidence, prediction):
    """改進的比分預測（修正版）."""
    
    home_avg = home_strength['avg_goals_scored']
    away_avg = away_strength['avg_goals_scored']
    
    # 初始化進球數
    home_goals = 1
    away_goals = 1
    
    if prediction == 'home_win':
        # 主隊贏
        home_base = max(1, round(home_avg * 1.2))
        away_base = max(0, round(away_avg * 0.7))
        
        if confidence > 70:
            home_goals = min(4, home_base + 1)
            away_goals = max(0, away_base - 1)
        elif confidence > 60:
            home_goals = home_base
            away_goals = away_base
        else:
            home_goals = max(1, home_base - 1)
            away_goals = max(0, away_base)
        
        # 確保主隊贏
        if home_goals <= away_goals:
            home_goals = away_goals + 1
            
    elif prediction == 'away_win':
        # 客隊贏
        home_base = max(0, round(home_avg * 0.7))
        away_base = max(1, round(away_avg * 1.2))
        
        if confidence > 70:
            away_goals = min(4, away_base + 1)
            home_goals = max(0, home_base - 1)
        elif confidence > 60:
            away_goals = away_base
            home_goals = home_base
        else:
            away_goals = max(1, away_base - 1)
            home_goals = max(0, home_base)
        
        # 確保客隊贏
        if away_goals <= home_goals:
            away_goals = home_goals + 1
            
    else:  # draw
        # 平局
        avg_total = (home_avg + away_avg) / 2
        
        if avg_total < 1.0:
            home_goals = away_goals = 0
        elif avg_total < 1.5:
            home_goals = away_goals = 1
        elif avg_total < 2.5:
            home_goals = away_goals = 1
        else:
            home_goals = away_goals = 2
    
    # 限制最高比分
    home_goals = min(5, max(0, home_goals))
    away_goals = min(5, max(0, away_goals))
    
    return f"{home_goals}-{away_goals}"

def predict_match(home_team, away_team):
    """預測比賽結果（修正版）."""
    
    home_team = normalize_team_name(home_team)
    away_team = normalize_team_name(away_team)
    
    try:
        with open('data/team_stats.json', 'r', encoding='utf-8') as f:
            team_stats = json.load(f)
    except FileNotFoundError:
        return {'error': '找不到球隊統計檔案'}
    
    if home_team not in team_stats:
        return {'error': f'找不到球隊統計: {home_team}'}
    if away_team not in team_stats:
        return {'error': f'找不到球隊統計: {away_team}'}
    
    home_strength = calculate_team_strength(team_stats[home_team], is_home=True)
    away_strength = calculate_team_strength(team_stats[away_team], is_home=False)
    
    home_advantage = 10
    home_total = home_strength['total'] + home_advantage
    away_total = away_strength['total']
    
    total_strength = home_total + away_total
    
    if total_strength > 0:
        home_base_prob = (home_total / total_strength) * 100
        away_base_prob = (away_total / total_strength) * 100
    else:
        home_base_prob = 50
        away_base_prob = 50
    
    strength_diff = abs(home_total - away_total)
    
    if strength_diff < 5:
        draw_prob = 35
    elif strength_diff < 10:
        draw_prob = 30
    elif strength_diff < 15:
        draw_prob = 25
    elif strength_diff < 20:
        draw_prob = 20
    else:
        draw_prob = 15
    
    remaining = 100 - draw_prob
    home_win_prob = (home_base_prob / (home_base_prob + away_base_prob)) * remaining
    away_win_prob = remaining - home_win_prob
    
    home_win_prob = round(home_win_prob, 1)
    away_win_prob = round(away_win_prob, 1)
    draw_prob = round(100 - home_win_prob - away_win_prob, 1)
    
    if home_win_prob > away_win_prob and home_win_prob > draw_prob:
        prediction = 'home_win'
        confidence = home_win_prob
    elif away_win_prob > home_win_prob and away_win_prob > draw_prob:
        prediction = 'away_win'
        confidence = away_win_prob
    else:
        prediction = 'draw'
        confidence = draw_prob
    
    expected_score = predict_score_improved(home_strength, away_strength, confidence, prediction)
    
    return {
        'prediction': prediction,
        'confidence': round(confidence, 1),
        'probabilities': {
            'home_win': home_win_prob,
            'draw': draw_prob,
            'away_win': away_win_prob,
        },
        'expected_score': expected_score,
        'analysis': {
            'home_team': home_team,
            'away_team': away_team,
            'home_form': team_stats[home_team].get('recent_form', 'N/A'),
            'away_form': team_stats[away_team].get('recent_form', 'N/A'),
            'home_form_score': home_strength['form'],
            'away_form_score': away_strength['form'],
            'home_win_rate': home_strength['win_rate'],
            'away_win_rate': away_strength['win_rate'],
            'home_avg_goals': home_strength['avg_goals_scored'],
            'away_avg_goals': away_strength['avg_goals_scored'],
            'home_total_score': home_strength['total'],
            'away_total_score': away_strength['total'],
        }
    }

if __name__ == "__main__":
    # 測試
    tests = [
        ('West Ham', 'Manchester City'),
        ('Barcelona', 'Sevilla'),
        ('Bayern Munich', 'Leverkusen'),
    ]
    
    for home, away in tests:
        print(f"\n{'='*70}")
        print(f"⚽ {home} vs {away}")
        print('='*70)
        result = predict_match(home, away)
        if 'error' not in result:
            print(f"預測: {result['prediction']} (信心度 {result['confidence']}%)")
            print(f"比分: {result['expected_score']}")
            print(f"機率: 主勝 {result['probabilities']['home_win']}% | "
                  f"和局 {result['probabilities']['draw']}% | "
                  f"客勝 {result['probabilities']['away_win']}%")
        else:
            print(f"錯誤: {result['error']}")

"""Test API-Football connection and fetch recent matches."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from app.config import settings
from datetime import datetime, timedelta

API_KEY = settings.football_api_key
BASE_URL = settings.football_api_base_url
headers = {'x-apisports-key': API_KEY}

print('='*60)
print('🔍 API-Football 連線測試')
print('='*60)
print(f'API Key: {API_KEY[:10]}...')
print(f'Base URL: {BASE_URL}')

# 測試 1: 最近 7 天的比賽
print('\n1️⃣ 測試最近 7 天 Premier League 比賽...')
start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
end = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

try:
    response = requests.get(
        f'{BASE_URL}/fixtures',
        headers=headers,
        params={'league': 39, 'from': start, 'to': end},
        timeout=10
    )
    
    print(f'   狀態碼: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        matches = data.get('response', [])
        print(f'   ✅ 找到 {len(matches)} 場比賽 ({start} ~ {end})')
        
        if matches:
            print(f'\n   最近 5 場:')
            for m in matches[:5]:
                fixture = m['fixture']
                teams = m['teams']
                date = fixture['date'][:10]
                home = teams['home']['name']
                away = teams['away']['name']
                status = fixture['status']['long']
                print(f'      {date} | {home} vs {away} ({status})')
        else:
            print('   ⚠️ 這段時間沒有比賽')
    else:
        print(f'   ❌ API 錯誤: {response.status_code}')
        print(f'   回應: {response.text[:200]}')
        
except Exception as e:
    print(f'   ❌ 連線失敗: {e}')

# 測試 2: 查詢當前賽季
print('\n2️⃣ 測試查詢 2025/26 賽季資料...')
try:
    response = requests.get(
        f'{BASE_URL}/fixtures',
        headers=headers,
        params={'league': 39, 'season': 2025},
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        matches = data.get('response', [])
        print(f'   ✅ 2025/26 賽季共 {len(matches)} 場比賽')
        
        if matches:
            # 統計狀態
            finished = sum(1 for m in matches if m['fixture']['status']['short'] == 'FT')
            upcoming = sum(1 for m in matches if m['fixture']['status']['short'] == 'NS')
            print(f'   已完成: {finished} 場')
            print(f'   未開始: {upcoming} 場')
    else:
        print(f'   ❌ 錯誤: {response.status_code}')
        
except Exception as e:
    print(f'   ❌ 失敗: {e}')

# 測試 3: 檢查配額
print('\n3️⃣ 檢查 API 配額...')
if response.headers:
    quota = response.headers.get('x-ratelimit-requests-remaining')
    limit = response.headers.get('x-ratelimit-requests-limit')
    if quota and limit:
        print(f'   剩餘請求: {quota}/{limit}')
    else:
        print('   無法取得配額資訊')

print('\n' + '='*60)
print('✅ 測試完成')
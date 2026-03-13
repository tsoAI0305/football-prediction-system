"""Debug API-Football queries."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from app.config import settings

API_KEY = settings.football_api_key
BASE_URL = settings.football_api_base_url

print("="*70)
print("🔍 API-Football 深度診斷")
print("="*70)
print(f"API Key: {API_KEY[:10]}...{API_KEY[-5:]}")
print(f"Base URL: {BASE_URL}")

headers = {'x-apisports-key': API_KEY}

# 測試 1: 檢查 API 狀態和配額
print("\n1️⃣ 檢查 API 狀態...")
try:
    response = requests.get(f"{BASE_URL}/status", headers=headers, timeout=10)
    print(f"   狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        account = data.get('response', {}).get('account', {})
        requests_info = data.get('response', {}).get('requests', {})
        
        print(f"   帳號類型: {account}")
        print(f"   今日已用: {requests_info.get('current', 'N/A')}")
        print(f"   今日限制: {requests_info.get('limit_day', 'N/A')}")
    else:
        print(f"   回應: {response.text}")
        
except Exception as e:
    print(f"   ❌ 錯誤: {e}")

# 測試 2: 查詢 Premier League 資訊
print("\n2️⃣ 查詢 Premier League (ID: 39) 資訊...")
try:
    response = requests.get(
        f"{BASE_URL}/leagues",
        headers=headers,
        params={'id': 39},
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        league = data.get('response', [{}])[0]
        seasons = league.get('seasons', [])
        
        print(f"   聯賽: {league.get('league', {}).get('name')}")
        print(f"\n   可用賽季:")
        for season in seasons[-5:]:  # 最近 5 個賽季
            year = season.get('year')
            current = season.get('current')
            start = season.get('start')
            end = season.get('end')
            print(f"      {year}: {start} ~ {end} {'← 當前' if current else ''}")
            
except Exception as e:
    print(f"   ❌ 錯誤: {e}")

# 測試 3: 嘗試不同賽季查詢
print("\n3️⃣ 測試不同賽季的比賽數量...")
for season in [2025, 2024, 2023]:
    try:
        response = requests.get(
            f"{BASE_URL}/fixtures",
            headers=headers,
            params={'league': 39, 'season': season},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get('response', [])
            print(f"   {season}/{season+1}: {len(matches)} 場比賽")
            
            # 檢查 headers 中的配額資訊
            if season == 2025:
                remaining = response.headers.get('x-ratelimit-requests-remaining')
                limit = response.headers.get('x-ratelimit-requests-limit')
                if remaining and limit:
                    print(f"      (剩餘請求: {remaining}/{limit})")
        else:
            print(f"   {season}/{season+1}: 錯誤 {response.status_code}")
            if response.status_code == 499:
                print(f"      → 可能是免費版無法存取此資料")
            print(f"      {response.text[:150]}")
            
    except Exception as e:
        print(f"   {season}/{season+1}: {e}")

# 測試 4: 查詢「最近」的比賽（不指定賽季）
print("\n4️⃣ 查詢最近 30 天的比賽（不指定賽季）...")
from datetime import datetime, timedelta

try:
    today = datetime.now()
    from_date = (today - timedelta(days=15)).strftime('%Y-%m-%d')
    to_date = (today + timedelta(days=15)).strftime('%Y-%m-%d')
    
    response = requests.get(
        f"{BASE_URL}/fixtures",
        headers=headers,
        params={
            'league': 39,
            'from': from_date,
            'to': to_date,
        },
        timeout=15
    )
    
    if response.status_code == 200:
        data = response.json()
        matches = data.get('response', [])
        print(f"   {from_date} ~ {to_date}: {len(matches)} 場比賽")
        
        if matches:
            print(f"\n   最近 3 場:")
            for m in matches[:3]:
                f = m['fixture']
                t = m['teams']
                g = m.get('goals', {})
                print(f"      {f['date'][:10]} | {t['home']['name']} {g.get('home', '?')}-{g.get('away', '?')} {t['away']['name']}")
    else:
        print(f"   ❌ 錯誤: {response.status_code}")
        
except Exception as e:
    print(f"   ❌ {e}")

# 測試 5: 查詢今天的「所有」比賽
print("\n5️⃣ 查詢今天所有聯賽的比賽...")
try:
    today = datetime.now().strftime('%Y-%m-%d')
    
    response = requests.get(
        f"{BASE_URL}/fixtures",
        headers=headers,
        params={'date': today},
        timeout=15
    )
    
    if response.status_code == 200:
        data = response.json()
        matches = data.get('response', [])
        print(f"   今天 ({today}) 全球所有比賽: {len(matches)} 場")
        
        if matches:
            # 統計聯賽
            leagues = {}
            for m in matches:
                league = m['league']['name']
                leagues[league] = leagues.get(league, 0) + 1
            
            print(f"\n   前 5 個聯賽:")
            for league, count in sorted(leagues.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"      {league}: {count} 場")
    else:
        print(f"   ❌ 錯誤: {response.status_code}")
        
except Exception as e:
    print(f"   ❌ {e}")

print("\n" + "="*70)
print("✅ 診斷完成")
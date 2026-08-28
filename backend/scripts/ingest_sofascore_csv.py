"""
scripts/ingest_sofascore_csv.py  (v2 — 支援比分欄位)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import csv, glob
from datetime import datetime
from app.database import SessionLocal
from app.models.match import Match

LEAGUE_MAP = {
    "bundesliga":"Bundesliga","epl":"Premier League",
    "premier_league":"Premier League","laliga":"La Liga",
    "la_liga":"La Liga","ligue_1":"Ligue 1","serie_a":"Serie A",
}
STATUS_MAP = {
    "finished":"FINISHED","scheduled":"SCHEDULED",
    "canceled":"CANCELED","postponed":"CANCELED","inprogress":"SCHEDULED",
}

def detect_league(filepath):
    name = os.path.basename(filepath).lower()
    for key, league in LEAGUE_MAP.items():
        if key in name: return league
    return None

def parse_dt(s):
    for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M","%Y-%m-%d"):
        try: return datetime.strptime(s.strip(), fmt)
        except: continue
    return None

def to_int(val):
    try: return int(val) if val != "" else None
    except: return None

def ingest_file(filepath, db):
    league = detect_league(filepath)
    if not league:
        print(f"  ⚠️  skip: {filepath}"); return {"skip":1}
    created=updated=skipped=0
    with open(filepath, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            home=(row.get("home") or row.get("home_team","")).strip()
            away=(row.get("away") or row.get("away_team","")).strip()
            dt=parse_dt(row.get("time_utc") or row.get("match_date") or "")
            status=STATUS_MAP.get((row.get("status") or "scheduled").lower().strip(),"SCHEDULED")
            hs=to_int(row.get("home_score",""))
            as_=to_int(row.get("away_score",""))
            if not home or not away or not dt: skipped+=1; continue
            ex=db.query(Match).filter(Match.home_team==home,Match.away_team==away,Match.match_date==dt).first()
            if not ex:
                ex=db.query(Match).filter(
                    Match.home_team==home,Match.away_team==away,
                    Match.match_date>=dt.replace(hour=0,minute=0,second=0),
                    Match.match_date<=dt.replace(hour=23,minute=59,second=59),
                ).first()
            if ex:
                changed=False
                if hs is not None and ex.home_score is None: ex.home_score=hs; changed=True
                if as_ is not None and ex.away_score is None: ex.away_score=as_; changed=True
                if ex.status!=status: ex.status=status; changed=True
                if ex.match_date!=dt: ex.match_date=dt; changed=True
                if changed: updated+=1
            else:
                db.add(Match(league=league,match_date=dt,home_team=home,away_team=away,
                             home_score=hs,away_score=as_,status=status))
                created+=1
    db.commit()
    return {"created":created,"updated":updated,"skipped":skipped}

def main():
    data_dir=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"data")
    files=list(set(f for p in [
        os.path.join(data_dir,"*fixtures*sofascore*.csv"),
        os.path.join(data_dir,"*sofascore*fixtures*.csv"),
    ] for f in glob.glob(p)))
    if not files: print("❌ 找不到任何 fixtures CSV"); sys.exit(1)
    print(f"找到 {len(files)} 個 fixtures CSV\n")
    db=SessionLocal(); total={"created":0,"updated":0,"skipped":0}
    try:
        for f in sorted(files):
            print(f"處理: {os.path.basename(f)}")
            r=ingest_file(f,db)
            for k in total: total[k]+=r.get(k,0)
            print(f"  ✅ created={r.get('created',0)} updated={r.get('updated',0)} skipped={r.get('skipped',0)}")
        print(f"\n{'='*50}")
        print(f"✅ 完成！created={total['created']} updated={total['updated']} skipped={total['skipped']}")
        tm=db.query(Match).count()
        fi=db.query(Match).filter(Match.status=="FINISHED").count()
        print(f"📊 DB 總比賽數: {tm}  已完賽: {fi}")
    except Exception as e:
        db.rollback(); print(f"\n❌ 錯誤: {e}"); raise
    finally: db.close()

if __name__=="__main__": main()

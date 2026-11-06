import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import WORK
import urllib.request, concurrent.futures as cf
STATSBOMB_COMMIT='4b73468fc5b0f1950f9f66fada70ad3a4f9327cb'  # pinned open-data version
B=f'https://raw.githubusercontent.com/statsbomb/open-data/{STATSBOMB_COMMIT}/data/'
def get(p):
    for i in range(4):
        try:
            return json.load(urllib.request.urlopen(B+p, timeout=120))
        except Exception as e:
            err=e
    raise err
comps=[(11,s) for s in [37,38,39,40,41,21,22,23,24,25,26,27,2,1,4,42,90]]+[(16,41),(16,22),(16,26),(16,23),(16,24),(16,25),(16,27),(16,2),(16,1),(16,4),(16,21),(16,37),(16,39),(43,3)]
matches=[]
for c,s in comps:
    for m in get(f'matches/{c}/{s}.json'):
        names=[m['home_team']['home_team_name'],m['away_team']['away_team_name']]
        if 'Barcelona' in names or 'Argentina' in names:
            matches.append(m)
print(len(matches),'matches',file=sys.stderr)
MESSI='Lionel Andrés Messi Cuccittini'
def proc(m):
    ev=get(f"events/{m['match_id']}.json")
    nick={}
    try:
        for t in get(f"lineups/{m['match_id']}.json"):
            for p in t['lineup']: nick[p['player_name']]=p.get('player_nickname') or p['player_name']
    except Exception: pass
    byid={e['id']:e for e in ev}
    messi_team=None; out=[]; played=False
    for e in ev:
        if e.get('player',{}).get('name')==MESSI: played=True; messi_team=e['team']['name']
    if not played: return m,[]
    # find goals scored by messi's team
    for e in ev:
        if e['type']['name']!='Shot' or e['shot']['outcome']['name']!='Goal': continue
        if e['team']['name']!=messi_team: continue
        shooter=e['player']['name']; kp=e['shot'].get('key_pass_id')
        assister=byid[kp]['player']['name'] if kp and kp in byid else None
        rec=dict(minute=e['minute'],second=e['second'],period=e['period'],x=e['location'][0],y=e['location'][1],
                 end=e['shot'].get('end_location'),body=e['shot']['body_part']['name'],shot_type=e['shot']['type']['name'],
                 technique=e['shot'].get('technique',{}).get('name'),play=e.get('play_pattern',{}).get('name'),
                 xg=e['shot'].get('statsbomb_xg'))
        if shooter==MESSI:
            rec.update(kind='Goal',assisted_by=nick.get(assister,assister) if assister else None); out.append(rec)
        elif assister==MESSI and byid[kp]['type']['name']=='Pass' and byid[kp]['pass'].get('goal_assist'):
            rec.update(kind='Assist',scorer=nick.get(shooter,shooter),pass_x=byid[kp]['location'][0],pass_y=byid[kp]['location'][1],
                       pass_type=byid[kp]['pass'].get('height',{}).get('name')); out.append(rec)
    # assists flagged on passes but whose shot lacks key_pass (safety)
    return m,out
res=[]
with cf.ThreadPoolExecutor(16) as ex:
    for i,(m,out) in enumerate(ex.map(proc,matches)):
        res.append(dict(match=dict(id=m['match_id'],date=m['match_date'],comp=m['competition']['competition_name'],season=m['season']['season_name'],
            home=m['home_team']['home_team_name'],away=m['away_team']['away_team_name'],hs=m['home_score'],as_=m['away_score'],
            stage=m.get('competition_stage',{}).get('name')),contribs=out))
json.dump(res,open(WORK+'sb/sb_messi.json','w'))
print('done',sum(len(r['contribs']) for r in res),file=sys.stderr)

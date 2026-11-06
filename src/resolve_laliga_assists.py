"""Find the La Liga assists Transfermarkt credits but StatsBomb does not.

For each La Liga match where Transfermarkt's assist count is higher than StatsBomb's
goal_assist flags, look at every teammate goal in StatsBomb's event data and mark it
as a candidate when Messi made the last pass of the move (with no other key pass) or
took the shot that was saved and scored on the rebound. build.py only accepts the
candidates when their number equals the gap exactly; otherwise the match report decides.
Writes WORK/tm/ll_cands.json.
"""
import json, glob, datetime, urllib.request, concurrent.futures as cf, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import WORK, CUTOFF
STATSBOMB_COMMIT = '4b73468fc5b0f1950f9f66fada70ad3a4f9327cb'
B = f'https://raw.githubusercontent.com/statsbomb/open-data/{STATSBOMB_COMMIT}/data/events/'
M = 'Lionel Andrés Messi Cuccittini'

tm = {}
for f in glob.glob(WORK + 'tm/club_*.json'):
    for t in json.load(open(f)):
        if t['section'] == 'LaLiga' and t['assists'].strip().isdigit():
            d = datetime.datetime.strptime(t['date'], '%m/%d/%y').strftime('%Y-%m-%d')
            tm[d] = tm.get(d, 0) + int(t['assists'])
sb = {r['match']['date']: r for r in json.load(open(WORK + 'sb/sb_messi.json')) if r['match']['comp'] == 'La Liga'}
need = sorted(d for d in sb if d <= CUTOFF and tm.get(d, 0) != sum(1 for c in sb[d]['contribs'] if c['kind'] == 'Assist'))

def cands(d):
    m = sb[d]['match']
    ev = json.load(urllib.request.urlopen(B + f"{m['id']}.json", timeout=120))
    out = []
    for i, e in enumerate(ev):
        if not (e['type']['name'] == 'Shot' and e['shot']['outcome']['name'] == 'Goal'
                and e['team']['name'] == 'Barcelona' and e['player']['name'] != M):
            continue
        prev = [x for x in ev[max(0, i - 25):i] if x.get('possession') == e['possession']
                and x.get('team', {}).get('name') == 'Barcelona'
                and x['type']['name'] in ('Pass', 'Shot', 'Carry', 'Dribble', 'Ball Receipt*')]
        acts = [x for x in prev if x['type']['name'] in ('Pass', 'Shot')]
        last = acts[-1] if acts else None
        kp = e['shot'].get('key_pass_id')
        reason = None
        if last and last['player']['name'] == M:
            if last['type']['name'] == 'Shot':
                reason = 'Messi shot, rebound'
            elif not kp or kp == last['id']:
                reason = 'Messi last pass'
        out.append(dict(min=e['minute'] + 1, period=e['period'], scorer=e['player']['name'], reason=reason,
                        x=e['location'][0], y=e['location'][1], body=e['shot']['body_part']['name'],
                        stype=e['shot']['type']['name'], xg=e['shot'].get('statsbomb_xg'),
                        px=last['location'][0] if last and reason else None,
                        py=last['location'][1] if last and reason else None,
                        already=(kp is not None and any(x['id'] == kp and x['player']['name'] == M
                                 and x.get('pass', {}).get('goal_assist') for x in ev))))
    return d, out

res = {}
with cf.ThreadPoolExecutor(8) as ex:
    for d, out in ex.map(cands, need):
        res[d] = out
json.dump(res, open(WORK + 'tm/ll_cands.json', 'w'))
print(len(need), 'La Liga matches where Transfermarkt and StatsBomb counts differ')

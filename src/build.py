import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import WORK, RAW as _RAW, OUT
import csv,json,re,sys
from collections import defaultdict,Counter
S=WORK
def fix(s):
    for _ in range(3):
        try: s2=s.encode('latin-1').decode('utf-8')
        except Exception: break
        if s2==s: break
        s=s2
    return s.strip()
def pdate(s):
    m,d,y=map(int,re.findall(r'\d+',s)); return f'20{y:02d}-{m:02d}-{d:02d}'
def pscore(s):
    a,b=s.split(':'); return int(re.match(r'\d+',a.strip()).group()),int(re.match(r'\d+',b.strip()).group())
def mkey(m):
    m=m.strip(); b=m.split('+'); return int(b[0])+(int(b[1])/100 if len(b)>1 else 0)
COMP={'LaLiga':'La Liga','UEFA Champions League':'Champions League','Champions League':'Champions League','Copa del Rey':'Copa del Rey',
 'Supercopa':'Supercopa de España','FIFA Club World Cup':'Club World Cup','UEFA Super Cup':'UEFA Super Cup'}
kag=[x for x in csv.DictReader(open(S+'ext/Lionel-Messi-Club-Career-Goals-Analysis/data.csv',encoding='latin-1')) if x['Club']=='FC Barcelona']
m800=[x for x in csv.DictReader(open(S+'ext/messi-800-goals-dataset/messi_goals.csv')) if x['date']<='2021-05-16']
sb=json.load(open(S+'sb/sb_messi.json'))
INTL={'IF':'International Friendly','WCQ':'World Cup Qualifier','CA':'Copa América','WC':'World Cup'}
m8b=defaultdict(list); m8a=[]
for x in m800:
    (m8a if x['competition'] in INTL else m8b[x['date']]).append(x)
sbg=defaultdict(list); sbm={}
for r in sb:
    m=r['match']
    for c in r['contribs']:
        c['_m']=m
        if c['kind']=='Goal': sbg[(m['date'],m['comp'])].append(c)
for k in sbg: sbg[k].sort(key=lambda c:(c['period'],c['minute'],c['second']))
def body_m8(b): return {'1':'Left Foot','2':'Right Foot','3':'Head'}.get(b)
def loc_m8(x):
    try: return round(100-int(x['shot_x']),1), round(int(x['shot_y']),1)
    except: return None,None
def loc_sb(x,y): return round(x/120*100,1), round(y/80*100,1)
rows=[]; issues=[]
# group kaggle by date
kd=defaultdict(list)
for x in kag: kd[pdate(x['Date'])].append(x)
oppmap={}
for d,lst in sorted(kd.items()):
    lst.sort(key=lambda x:mkey(x['Minute']))
    m8=m8b.get(d,[])
    if len(m8)!=len(lst): issues.append(('m800 count',d,len(lst),len(m8))); m8=[]
    comp=COMP[lst[0]['Competition']]
    sbl=sbg.get((d,comp),[]) if comp in ('La Liga','Champions League') else []
    if sbl and len(sbl)!=len(lst): issues.append(('sb count',d,len(lst),len(sbl))); sbl=[]
    for i,x in enumerate(lst):
        h,a=pscore(x['Result']); ah,aa=pscore(x['At_score'])
        ven=x['Venue']; fs,os_=(h,a) if ven=='H' else (a,h)
        typ=x['Type']; gtype='Penalty' if 'Penalty' in typ and 'rebound' not in typ else 'Free Kick' if 'free kick' in typ else 'Open Play'
        r=dict(kind='Goal',date=d,team='Barcelona',comp=comp,stage=x['Matchday'],opp=fix(x['Opponent']),venue=ven,
               fs=fs,os=os_,minute=x['Minute'].strip(),score_after=f"{ah if ven=='H' else aa}-{aa if ven=='H' else ah}",
               gtype=gtype,detail=typ,partner=fix(x['Goal_assist']) or None,body=None,x=None,y=None,locsrc=None,xg=None,technique=None)
        if typ=='Header': r['body']='Head'
        elif 'Left' in typ: r['body']='Left Foot'
        elif 'Right' in typ: r['body']='Right Foot'
        if m8:
            mm=m8[i]; b=body_m8(mm['body_part'])
            if r['body'] and b and r['body']!=b: issues.append(('body conflict',d,r['body'],b))
            r['body']=r['body'] or b; r['x'],r['y']=loc_m8(mm); r['locsrc']='video'
            if mm['finish_type']: r['technique']=mm['finish_type']
        if sbl:
            c=sbl[i]; r['_v']=(r['x'],r['y']) if r['locsrc']=='video' else None; r['body']=c['body'] if c['body']!='Other' else r['body']; r['x'],r['y']=loc_sb(c['x'],c['y']); r['locsrc']='statsbomb'
            r['xg']=round(c['xg'],3) if c['xg'] else None; r['technique']=c['technique'] if c['technique']!='Normal' else r['technique']
            if c.get('assisted_by'): r['partner']=c['assisted_by']
            r['gtype']=c['shot_type'] if c['shot_type']!='Open Play' else r['gtype']
            sbopp=c['_m']['away'] if c['_m']['home']=='Barcelona' else c['_m']['home']; oppmap[r['opp']]=sbopp
            fs2,os2=(c['_m']['hs'],c['_m']['as_']) if c['_m']['home']=='Barcelona' else (c['_m']['as_'],c['_m']['hs'])
            if (fs2,os2)!=(fs,os_): issues.append(('score conflict',d,fs,os_,fs2,os2))
        rows.append(r)
for r in rows: r['opp']=oppmap.get(r['opp'],r['opp'])
# international goals
for x in m8a:
    X,Y=loc_m8(x)
    rows.append(dict(kind='Goal',date=x['date'],team='Argentina',comp=INTL[x['competition']],stage=None,opp=x['opponent'],
        venue='H' if x['is_home']=='1' else 'A',fs=None,os=None,minute=None,score_after=None,
        gtype={'0':'Open Play','1':'Penalty','2':'Free Kick','3':'Open Play'}.get(x['goal_type'],'Open Play'),detail=None,
        partner=None if x['assist_player'] in ('none','unknown','','Messi') else x['assist_player'],body=body_m8(x['body_part']),
        x=X,y=Y,locsrc='video',xg=None,technique=x['finish_type'] or None))
import unicodedata
def strip(t): return ''.join(c for c in unicodedata.normalize('NFD',t) if unicodedata.category(c)!='Mn').lower()
# ---- Wikipedia enrichment for Argentina goals ----
import datetime as _dt
wiki=json.load(open(S+'wiki_intl.json')); wmin=json.load(open(S+'wiki_minutes.json'))
venue={}
for f in ['wiki/res0019.txt','wiki/Argentina_national_football_team_results_2020-present.txt']:
    t=open(S+f).read()
    for m in re.finditer(r'\{\{dts\|([^}]*)\}\}\s*\n\|[^\n]*\((H|A|N)\)',t):
        try: d=_dt.datetime.strptime(m.group(1).replace('|',' ').strip(),'%d %B %Y').strftime('%Y-%m-%d')
        except ValueError: continue
        venue[d]=m.group(2)
FB={'CRO':'Croatia','SCG':'Serbia and Montenegro','SLO':'Slovenia','ALG':'Algeria','PER':'Peru','MEX':'Mexico','VEN':'Venezuela','BOL':'Bolivia','GUA':'Guatemala','URU':'Uruguay','ECU':'Ecuador','PAR':'Paraguay','COL':'Colombia','CHI':'Chile','BRA':'Brazil','FRA':'France','ESP':'Spain','POR':'Portugal','ALB':'Albania','SUI':'Switzerland','GER':'Germany','BIH':'Bosnia and Herzegovina','IRN':'Iran','NGA':'Nigeria','SVN':'Slovenia','HKG':'Hong Kong','CRC':'Costa Rica','PAN':'Panama','USA':'United States','HAI':'Haiti','NIC':'Nicaragua','KSA':'Saudi Arabia','ISL':'Iceland','IRQ':'Iraq','SRB':'Serbia','JAM':'Jamaica','EGY':'Egypt'}
arg=[r for r in rows if r['team']=='Argentina' and r['kind']=='Goal']
if len(arg)!=len(wiki): issues.append(('intl total',len(arg),len(wiki)))
from collections import Counter as _C
for r,w in zip(arg,wiki):
    d0=_dt.date.fromisoformat(r['date']); d1=_dt.date.fromisoformat(w['date'])
    nm=FB.get(w['opp'],w['opp'])
    if abs((d0-d1).days)>1 or (strip(nm.replace(' ',''))[:5]!=strip(r['opp'].replace(' ',''))[:5] and w['opp']!='SCG'):
        issues.append(('intl align',r['date'],r['opp'],w['date'],nm))
    r['date']=w['date']; r['opp']=nm
wmin_used=_C()
for r,w in zip(arg,wiki):
    a,b=map(int,w['result'].split('–')); r['fs'],r['os']=a,b
    r['score_after']=w['score_at']
    if w['pen']: r['gtype']='Penalty'
    elif r['gtype']=='Penalty': issues.append(('pen conflict',w['date'])); r['gtype']='Open Play'
    ms=wmin.get(w['date'],[]); i=wmin_used[w['date']]; wmin_used[w['date']]+=1
    if i<len(ms): r['minute']=ms[i][0]
    r['venue']=venue.get(w['date'],r['venue'])
    c=w['comp']
    r['comp']='World Cup Qualifier' if 'qualification' in c else 'World Cup' if 'World Cup' in c else 'Copa América' if 'Copa' in c else 'International Friendly'
for d,ms in wmin.items():
    if d<='2021-05-16' and wmin_used[d]!=len(ms): issues.append(('minute count',d,wmin_used[d],len(ms)))
# WC2018 statsbomb enrich
for r in sb:
    m=r['match']
    if m['comp']!='FIFA World Cup': continue
    for c in r['contribs']:
        if c['kind']=='Goal':
            g=[z for z in rows if z['team']=='Argentina' and z['date']==m['date']][0]
            g.update(minute=str(c['minute']+1),fs=m['hs'] if m['home']=='Argentina' else m['as_'],os=m['as_'] if m['home']=='Argentina' else m['hs'],
                     xg=round(c['xg'],3),locsrc='statsbomb',venue='N'); g['x'],g['y']=loc_sb(c['x'],c['y'])
# assists from statsbomb
for r in sb:
    m=r['match']
    for c in r['contribs']:
        if c['kind']!='Assist': continue
        team='Argentina' if 'Argentina' in (m['home'],m['away']) else 'Barcelona'
        home=m['home']==team; X,Y=loc_sb(c['x'],c['y']); PX,PY=loc_sb(c['pass_x'],c['pass_y'])
        mn=c['minute']+1
        rows.append(dict(kind='Assist',date=m['date'],team=team,comp={'FIFA World Cup':'World Cup'}.get(m['comp'],m['comp']),stage=None,
            opp=m['away'] if home else m['home'],venue='N' if team=='Argentina' or m['comp']=='Champions League' else ('H' if home else 'A'),
            fs=m['hs'] if home else m['as_'],os=m['as_'] if home else m['hs'],minute=str(mn) if not((c['period']==1 and mn>45) or (c['period']==2 and mn>90)) else f"{45 if c['period']==1 else 90}+{mn-(45 if c['period']==1 else 90)}",
            score_after=None,gtype=c['shot_type'],detail=c['pass_type'],partner=c['scorer'],body=c['body'],x=X,y=Y,px=PX,py=PY,locsrc='statsbomb',xg=round(c['xg'],3) if c['xg'] else None,technique=c['technique'],assist_type='Pass'))
# match flags for intl venue
for r in rows:
    if r['comp'] in ('Champions League',) and r['stage']=='Final': r['venue']='N'

print(len(rows),Counter((r['team'],r['comp'],r['kind']) for r in rows),file=sys.stderr)
print('issues',len(issues),file=sys.stderr)
for i in issues: print(i,file=sys.stderr)
print(Counter(r['locsrc'] for r in rows),Counter(r['body'] for r in rows if r['kind']=='Goal'),file=sys.stderr)
import statistics as st
P=[(r['_v'],(r['x'],r['y'])) for r in rows if r.get('_v')]
print('pairs',len(P),'corrX',st.correlation([a[0] for a,b in P],[b[0] for a,b in P]),'corrY',st.correlation([a[1] for a,b in P],[b[1] for a,b in P]),'mdx',st.median(abs(a[0]-b[0]) for a,b in P),'mdy',st.median(abs(a[1]-b[1]) for a,b in P),file=sys.stderr)
for r in rows: r.pop('_v',None)
json.dump(rows,open(S+'merged_intermediate.json','w'),ensure_ascii=False,separators=(',',':'))
def _unused(t): return ''.join(c for c in unicodedata.normalize('NFD',t) if unicodedata.category(c)!='Mn').lower()
PMAP={'Aguero':'Sergio Agüero','Sergio Agüero':'Sergio Agüero','Alexandre Dimitri Song-Billong':'Alex Song','Antonio A05a':None,
 'Bojan':'Bojan Krkić','Bojan Krkic':'Bojan Krkić','DiMaria':'Ángel Di María','Higuain':'Gonzalo Higuaín','Lavezzi':'Ezequiel Lavezzi','Tevez':'Carlos Tevez',
 'Banega':'Éver Banega','Gaitan':'Nicolás Gaitán','Gago':'Fernando Gago','Riquelme':'Juan Román Riquelme','Lo Celso':'Giovani Lo Celso','Rojo':'Marcos Rojo',
 'Pavon':'Cristian Pavón','Ocampos':'Lucas Ocampos','Casco':'Milton Casco','Cruz':'Julio Cruz','Ronaldinho Gaacho':'Ronaldinho','Samuel Etoo':"Samuel Eto'o",
 'Marta Montoya':'Martín Montoya','Thiago':'Thiago Alcântara','Ã‰ric Abidal':'Éric Abidal'}
canon={}
for r in rows:
    p=r['partner']
    if not p: continue
    p=PMAP.get(p,p)
    if not p: r['partner']=None; continue
    k=strip(p)
    if k not in canon or (canon[k]==strip(canon[k]) and p!=k): canon[k]=p if not canon.get(k) or any(ord(c)>127 for c in p) else canon[k]
    r['partner']=p
for r in rows:
    if r['partner']: r['partner']=canon[strip(r['partner'])]
OMAP={'HongKong':'Hong Kong','RC Deportivo La Coruña':'Deportivo La Coruña','Levante UD':'Levante','Córdoba CF':'Córdoba','Real Murcia CF':'Real Murcia','Recreativo Huelva':'Recreativo','Bosnia':'Bosnia and Herzegovina'}
for r in rows: r['opp']=OMAP.get(r['opp'],r['opp'])
# ---- Transfermarkt match reports: assists outside StatsBomb coverage ----
import glob as _g, sys as _s
_s.path.insert(0,S+'tm'); 
RAW=_RAW
def _clean(x): return html.unescape(re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',x))).strip()
import html
TMC={'UEFA Champions League':'Champions League','Champions League':'Champions League','Copa del Rey':'Copa del Rey','Supercopa':'Supercopa de España','Supercopa de España':'Supercopa de España',
     'UEFA Super Cup':'UEFA Super Cup','FIFA Club World Cup':'Club World Cup','LaLiga':'La Liga'}
argcomp={}
for f in ['wiki/res0019.txt','wiki/Argentina_national_football_team_results_2020-present.txt']:
    t=open(S+f).read()
    for m in re.finditer(r'\{\{dts\|([^}]*)\}\}\s*\n\|[^\n]*\n\|[^\n]*\n\|[^\n]*\n\|([^\n]*)',t):
        try: d=_dt.datetime.strptime(m.group(1).replace('|',' ').strip(),'%d %B %Y').strftime('%Y-%m-%d')
        except ValueError: continue
        c=re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]',r'\1',m.group(2))
        argcomp[d]='World Cup Qualifier' if 'qualif' in c.lower() else 'World Cup' if 'World Cup' in c else 'Copa América' if 'Copa' in c else 'International Friendly'
def body_of(shot):
    return 'Left Foot' if 'Left' in shot else 'Right Foot' if 'Right' in shot else 'Head' if 'Header' in shot else None
tm_added=0; tm_enriched=0; tm_seen=set(); ll_removed=[]; goal_min_filled=[]
# report id -> local match date, from the season and national-team pages
iddate={}
for f in _g.glob(S+'tm/club_*.json')+[S+'tm/tm_arg.json']:
    for t_ in json.load(open(f)):
        if t_.get('report'): iddate[str(t_['report']).split('/')[-1]]=_dt.datetime.strptime(t_['date'],'%m/%d/%y').strftime('%Y-%m-%d')
tm_reports_used=[]
for f in sorted(_g.glob(RAW+'*.html')):
    t=open(f,encoding='utf-8',errors='replace').read()
    tt=re.search(r'<title>(.*?)</title>',t,re.S)
    if not tt or 'Match sheet' not in tt.group(1): continue
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S)
    title=_clean(tt.group(1))
    m=re.match(r'(.+?) - (.+?), (\w+ \d+, \d{4}) - (.+?) - Match sheet',title)
    home,away,ds,comp=m.groups()
    rid=re.search(r'og:url" content="[^"]*spielbericht/(\d+)',t)
    d=iddate.get(rid.group(1)) if rid else None
    d=d or _dt.datetime.strptime(ds,'%b %d, %Y').strftime('%Y-%m-%d')
    if d>'2021-05-16' or d in tm_seen: continue
    tm_seen.add(d); tm_reports_used.append(d)
    team='Argentina' if 'Argentina' in (home,away) else 'Barcelona'
    is_ll=team=='Barcelona' and TMC.get(comp,comp)=='La Liga'
    gs=t.find('sb-tore'); sec=t[gs:t.find('</ul>',t.find('<ul',gs))]
    evs=[]
    for side,b in re.findall(r'<li class="sb-aktion-(heim|gast)">(.*?)</li>',sec,re.S):
        pos=re.search(r'background-position:\s*(-?\d+)px\s+(-?\d+)px',b)
        mn=(-int(pos.group(2))//36)*10+(-int(pos.group(1))//36)+1 if pos else None
        ex=re.search(r'\+\s*(\d+)',_clean(re.search(r'sb-aktion-uhr">(.*?)</div>',b,re.S).group(1)))
        act=re.search(r'sb-aktion-aktion">(.*?)</div>',b,re.S).group(1).split('Assist:')
        _sa=re.search(r'<a[^>]*>(.*?)</a>',act[0],re.S); scorer=_clean(_sa.group(1)) if _sa else _clean(act[0]).split(',')[0].strip(); shot=_clean(re.sub(r'<a.*?</a>','',act[0],flags=re.S)).strip(', ').split(',')[0].strip()
        asst=atype=None
        if len(act)>1:
            _aa=re.search(r'<a[^>]*>(.*?)</a>',act[1],re.S); asst=_clean(_aa.group(1)) if _aa else _clean(act[1]).split(',')[0].strip(); atype=_clean(re.sub(r'<a.*?</a>','',act[1],flags=re.S)).strip(', ').split(',')[0].strip()
        evs.append(dict(side=side,minute=(f"{mn}+{ex.group(1)}" if ex else str(mn)),score=_clean(re.search(r'spielstand">(.*?)</div>',b,re.S).group(1)),scorer=scorer,shot=shot,assist=asst,atype=atype))
    if not evs: continue
    fh,fa=map(int,evs[-1]['score'].split(':'))
    myside='heim' if (home=='FC Barcelona' if team=='Barcelona' else home=='Argentina') else 'gast'
    fs,os_=(fh,fa) if myside=='heim' else (fa,fh)
    opp=away if myside=='heim' else home
    same=[r for r in rows if r['date']==d and r['team']==team]
    if same: opp=same[0]['opp']
    else: opp=OMAP.get(opp,opp) if 'OMAP' in globals() else opp
    c=TMC.get(comp,comp) if team=='Barcelona' else ('World Cup Qualifier' if 'qualif' in comp.lower() else 'World Cup' if 'World Cup' in comp else 'Copa América' if 'Copa' in comp else 'International Friendly')
    ven='H' if myside=='heim' else 'A'
    if same: ven=same[0]['venue']
    elif team=='Argentina': ven=venue.get(d,ven)
    if is_ll:
        credited={strip(e['scorer'])[:5] for e in evs if e['assist']=='Lionel Messi' and e['side']==myside and e['scorer']!='Lionel Messi'}
        for r_ in [r for r in rows if r['kind']=='Assist' and r['date']==d and r['team']=='Barcelona']:
            if strip(r_['partner'] or '')[:5] not in credited: rows.remove(r_); ll_removed.append((d,r_['partner']))
    for e in evs:
        if e['scorer']=='Lionel Messi' and e['side']==myside:
            sa=e['score'].replace(':','–') if myside=='heim' else '–'.join(e['score'].split(':')[::-1])
            for g_ in rows:
                if g_['kind']=='Goal' and g_['team']==team and g_['date']==d and not g_['minute'] and g_.get('score_after')==sa:
                    g_['minute']=e['minute']; goal_min_filled.append(d); break
    used=set()
    for e in evs:
        if e['assist']!='Lionel Messi' or e['side']!=myside or e['scorer']=='Lionel Messi': continue
        ex_=[r for r in rows if r['kind']=='Assist' and r['date']==d and id(r) not in used and r.get('locsrc')=='statsbomb' and strip(r['partner'] or '')[:5]==strip(e['scorer'])[:5]]
        if ex_: used.add(id(ex_[0]))
        if ex_:
            ex_[0]['assist_type']=None if re.match(r'^\d+\.',e['atype'] or '') else e['atype']; tm_enriched+=1; continue
        rows.append(dict(kind='Assist',date=d,team=team,comp=c,stage=None,opp=opp,venue=ven,fs=fs,os=os_,minute=e['minute'],score_after=e['score'] if myside=='heim' else ':'.join(e['score'].split(':')[::-1]),
            gtype='Penalty' if 'Penalty' in e['shot'] else 'Free Kick' if 'free kick' in e['shot'].lower() else 'Open Play',detail=e['shot'],partner=e['scorer'],body=body_of(e['shot']),
            x=None,y=None,locsrc=None,xg=None,technique=None,assist_type='Won penalty' if (e['atype'] or '').startswith('Penalty') else (None if re.match(r'^\d+\.',e['atype'] or '') else e['atype'])))
        tm_added+=1
# La Liga: reconcile StatsBomb assists to Transfermarkt per-match counts
tmll=Counter()
for f in _g.glob(S+'tm/club_*.json'):
    for t_ in json.load(open(f)):
        if t_['section']=='LaLiga' and t_['assists'].strip().isdigit(): tmll[_dt.datetime.strptime(t_['date'],'%m/%d/%y').strftime('%Y-%m-%d')]+=int(t_['assists'])
cands=json.load(open(S+'tm/ll_cands.json'))
sbm={r['match']['date']:r['match'] for r in sb if r['match']['comp']=='La Liga'}
ll_unresolved=[]; ll_inferred=0
for d in sorted(set(tmll)|{r['date'] for r in rows if r['kind']=='Assist' and r['comp']=='La Liga'}):
    if d>'2021-05-16': continue
    have=[r for r in rows if r['kind']=='Assist' and r['comp']=='La Liga' and r['date']==d]
    k=tmll[d]-len(have)
    if k==0: continue
    strong=[c for c in cands.get(d,[]) if c['reason'] and not c['already']]
    if k>0 and len(strong)==k and d in sbm:
        m_=sbm[d]; home=m_['home']=='Barcelona'
        for c in strong:
            mn=c['min']; per=c['period']
            mins=str(mn) if not((per==1 and mn>45) or (per==2 and mn>90)) else f"{45 if per==1 else 90}+{mn-(45 if per==1 else 90)}"
            X,Y=loc_sb(c['x'],c['y']); PX,PY=loc_sb(c['px'],c['py'])
            nm=next((p for p in canon.values() if strip(p)[:5]==strip(c['scorer'])[:5]),c['scorer'])
            rows.append(dict(kind='Assist',date=d,team='Barcelona',comp='La Liga',stage=None,opp=m_['away'] if home else m_['home'],venue='H' if home else 'A',
                fs=m_['hs'] if home else m_['as_'],os=m_['as_'] if home else m_['hs'],minute=mins,score_after=None,gtype=c['stype'],detail=None,partner=nm,
                body=c['body'] if c['body']!='Other' else None,x=X,y=Y,px=PX,py=PY,locsrc='statsbomb',xg=round(c['xg'],3) if c['xg'] else None,technique=None,
                assist_type='Shot on goal' if 'rebound' in c['reason'] else 'Pass'))
            ll_inferred+=1
    else: ll_unresolved.append((d,tmll[d],len(have)))
print('La Liga: inferred from StatsBomb',ll_inferred,'removed by report',ll_removed,'unresolved',ll_unresolved,file=sys.stderr)
# ---- Transfermarkt "All goals" page, Friendlies filter: minutes of Argentina friendly goals ----
from transfermarkt_goals import parse as _parse_goals
_pages=[f for f in sorted(_g.glob(RAW+'*.html'))
        if re.search(r'og:url" content="[^"]*/alletore/[^"]*wettbewerb=FS', open(f,encoding='utf-8',errors='replace').read(30000))]
if not _pages:
    sys.exit('ERROR: no saved Transfermarkt "All goals" page with the Friendlies filter in '+RAW+
             '. It supplies the minute of Argentina friendly goals. See README, "Rebuilding the data".')
fs_goals=[g for g in _parse_goals(_pages[0]) if g['team']=='Argentina' and '2004-10-16'<=g['date']<='2021-05-16']
if not fs_goals:
    sys.exit('ERROR: '+os.path.basename(_pages[0])+' has no senior Argentina goals. Save it again with the Friendlies filter on.')
fs_filled=[]; fs_partner=[]; fs_conflicts=[]; fs_unmatched=[]
for g_ in [r for r in rows if r['team']=='Argentina' and r['kind']=='Goal' and r['comp']=='International Friendly']:
    d0=_dt.date.fromisoformat(g_['date'])
    cands_=[t for t in fs_goals if abs((_dt.date.fromisoformat(t['date'])-d0).days)<=1
            and strip(t['opp'].replace(' ',''))[:5]==strip(g_['opp'].replace(' ',''))[:5]]
    def arg_first(t):  # Transfermarkt prints home:away
        a,b=t['at_score'].split(':'); return f"{a}–{b}" if t['venue']=='H' else f"{b}–{a}"
    hit=[t for t in cands_ if arg_first(t)==g_['score_after']]
    if len(hit)!=1: fs_unmatched.append((g_['date'],g_['opp'],g_['score_after'],len(hit))); continue
    t=hit[0]
    if not g_['minute']: g_['minute']=t['minute']; fs_filled.append(g_['date'])
    elif g_['minute']!=t['minute']: fs_conflicts.append((g_['date'],g_['opp'],'minute',g_['minute'],t['minute']))
    if (t['type']=='Penalty')!=(g_['gtype']=='Penalty'): fs_conflicts.append((g_['date'],g_['opp'],'penalty',g_['gtype'],t['type']))
    if t['assist'] and t['type']!='Penalty':
        if not g_['partner']: g_['partner']=t['assist']; fs_partner.append((g_['date'],t['assist']))
        elif strip(g_['partner'])[-5:]!=strip(t['assist'])[-5:]: fs_conflicts.append((g_['date'],g_['opp'],'assist',g_['partner'],t['assist']))
print('friendlies page: minutes filled',len(fs_filled),'assisters added',fs_partner,'conflicts',fs_conflicts,'unmatched',fs_unmatched,file=sys.stderr)
TMOPP={'Athletic Bilbao':'Athletic Club','Atlético de Madrid':'Atlético Madrid','CA Osasuna':'Osasuna','Granada CF':'Granada','Levante UD':'Levante',
 'RCD Espanyol Barcelona':'Espanyol','Sevilla FC':'Sevilla','Valencia CF':'Valencia','Villarreal CF':'Villarreal','Ferencvarosi TC':'Ferencváros',
 'Panathinaikos Athens':'Panathinaikos','SV Werder Bremen':'Werder Bremen','CD Numancia de Soria':'Numancia','Club Atletico de Ceuta':'AD Ceuta',
 'Club Estudiantes de La Plata':'Estudiantes','CA River Plate':'River Plate','CF Atlante':'Atlante','Benidorm CD':'Benidorm','Al-Sadd SC':'Al-Sadd',
 'FC Viktoria Plzen':'Viktoria Plzeň','SK Slavia Prague':'Slavia Prague','Olympiacos Piraeus':'Olympiacos'}
known={strip(r['partner']):r['partner'] for r in rows if r['partner'] and any(ord(ch)>127 for ch in r['partner'])}
known.update({strip(v):v for v in canon.values()})
for r in rows:
    r['opp']=TMOPP.get(r['opp'],r['opp'])
    if r['partner']: r['partner']=known.get(strip(r['partner']),r['partner'])
print('transfermarkt assists added',tm_added,'enriched',tm_enriched,'goal minutes filled',len(goal_min_filled),file=sys.stderr)
for r in rows:
    if r['kind']=='Goal' and r['gtype']=='Penalty': r['partner']=None
rows.sort(key=lambda r:(r['date'],r['kind']))
out=[]
for i,r in enumerate(rows):
    y,m=int(r['date'][:4]),int(r['date'][5:7]); s=y if m>=7 else y-1
    sc=f"{r['fs']}–{r['os']}" if r['fs'] is not None else None
    res=None if r['fs'] is None else ('W' if r['fs']>r['os'] else 'D' if r['fs']==r['os'] else 'L')
    tech=r.get('technique'); tech=None if tech in (None,'Normal','') else tech
    out.append(dict(id=i+1,date=r['date'],season=f"{s}/{str(s+1)[2:]}",kind=r['kind'],team=r['team'],comp=r['comp'],opp=r['opp'],
      venue=r['venue'],score=sc,result=res,minute=r['minute'],body=r['body'],gtype=r['gtype'],technique=tech,partner=r['partner'],assist_type=r.get('assist_type') if r['kind']=='Assist' else None,
      x=r['x'],y=r['y'],px=r.get('px'),py=r.get('py'),xg=r['xg'],locsrc=r['locsrc']))
json.dump(out,open(OUT+'messi_contributions.json','w'),ensure_ascii=False,separators=(',',':'))
import csv as _c
w=_c.DictWriter(open(OUT+'messi_contributions.csv','w',newline=''),fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print('final',len(out),Counter(o['season'] for o in out).most_common(3),file=sys.stderr)

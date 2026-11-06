import re,json,datetime,os,sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import WORK
t=open(WORK+'wiki/raw.txt').read()
t=t[t.find('{| class="wikitable sortable"'):]; t=t[:t.find('\n|}')]
t=re.sub(r'<ref[^>]*/>','',t); t=re.sub(r'<ref[^>]*>.*?</ref>','',t,flags=re.S)
rows=t.split('\n|-')
def split_cell(raw):
    d=0
    for i,ch in enumerate(raw):
        if raw[i:i+2] in ('{{','[['): d+=1
        elif raw[i:i+2] in ('}}',']]'): d-=1
        elif ch=='|' and d==0: return raw[:i],raw[i+1:]
    return '',raw
COLS=['cap','date','venue','opp','score','result','comp','ref']
carry={}; out=[]
for r in rows:
    lines=[l for l in r.strip().split('\n') if l.strip()]
    if not lines or not lines[0].startswith('!'): continue
    m=re.search(r'\|\s*(\d+)\s*$',lines[0])
    if not m: continue
    no=int(m.group(1))
    cells=[split_cell(l[1:].strip()) for l in lines[1:] if l.startswith('|')]
    rec={}; ci=0
    for c in COLS:
        if carry.get(c,(0,''))[0]>0:
            n,v=carry[c]; rec[c]=v; carry[c]=(n-1,v); continue
        if ci>=len(cells): rec[c]=None; continue
        attrs,val=cells[ci]; ci+=1
        if not ('=' in attrs) : val=(attrs+'|'+val) if attrs else val
        if not attrs:
            m2=re.match(r'^((?:[a-z]+="?[^"{|\s]*"?\s+)+)(\{\{.*)$',val)
            if m2: attrs,val=m2.group(1),m2.group(2)
        rs=re.search(r'rowspan="?(\d+)',attrs)
        if rs: carry[c]=(int(rs.group(1))-1,val.strip())
        rec[c]=val.strip()
    rec['no']=no; out.append(rec)
def clean(s):
    if s is None: return None
    s=re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]',r'\1',s); return s
res=[]
for r in out:
    if r["result"] is None or r["opp"] is None: print("BAD",r); continue
    if r['no']>71: break
    sc=r['score']; pen='double dagger' in sc
    res.append(dict(no=r['no'],date=datetime.datetime.strptime(clean(r['date']).strip(),'%d %B %Y').strftime('%Y-%m-%d'),
      opp=re.search(r'\{\{fb\|(\w+)',r['opp']).group(1),score_at=re.search(r'\d+–\d+',sc).group(),pen=pen,
      result=re.search(r'\d+–\d+',r['result']).group(),comp=clean(r['comp']),venue=clean(r['venue'])))
json.dump(res,open(WORK+'wiki_intl.json','w'),ensure_ascii=False,indent=0)
print(len(res)); [print(x) for x in res[:4]+res[-3:]]

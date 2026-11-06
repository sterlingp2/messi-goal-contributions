import re,glob,json,datetime,os,sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import WORK
out={}
def pdate(s):
    m=re.search(r'\{\{[Ss]tart date(?: and age)?\|(\d{4})\|(\d{1,2})\|(\d{1,2})',s)
    if m: return '%s-%02d-%02d'%(m.group(1),int(m.group(2)),int(m.group(3)))
    m=re.search(r'(\d{1,2}) (January|February|March|April|May|June|July|August|September|October|November|December) (\d{4})',s)
    if m: return datetime.datetime.strptime(m.group(0),'%d %B %Y').strftime('%Y-%m-%d')
    m=re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December) (\d{1,2}), (\d{4})',s)
    if m: return datetime.datetime.strptime(m.group(0),'%B %d, %Y').strftime('%Y-%m-%d')
for f in glob.glob(WORK+'wiki/t_*.txt'):
    t=open(f).read()
    for blk in re.split(r'\{\{\s*(?:#invoke:)?[Ff]ootball ?box',t)[1:]:
        if 'Messi' not in blk: continue
        dm=re.search(r'\|\s*date\s*=([^\n]*)',blk)
        if not dm: continue
        d=pdate(dm.group(1))
        mins=[]
        for g in re.finditer(r'Messi\]\]\s*\{\{goal\|([^}]*)\}\}',blk):
            parts=g.group(1).split('|')
            for i in range(0,len(parts),2):
                p=parts[i].strip()
                if p: mins.append((p,(parts[i+1].strip() if i+1<len(parts) else '')))
        if mins: out[d]=mins
json.dump(out,open(WORK+'wiki_minutes.json','w'),indent=0)
for k in sorted(out): print(k,out[k])

"""Parse saved Transfermarkt season and national-team stats pages (detailed view).

Reads every stats page in RAW and writes one JSON per page to WORK/tm/:
club_<season>.json for club seasons, tm_arg.json for the national team.
Each row is one match with Messi's goals and assists and the match-report id.
"""
import sys, re, json, glob, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import WORK, RAW
from html.parser import HTMLParser
class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.stack=[]; s.rows=[]; s.cur=None; s.cell=None; s.depth=0; s.sections=[]; s.heads=[]; s.inhead=None
    def handle_starttag(s,tag,a):
        a=dict(a); s.depth+=1
        if tag=='h2' or (tag=='div' and 'content-box-headline' in (a.get('class') or '')): s.inhead=s.depth; s.heads.append('')
        if a.get('role')=='row' and tag=='div': s.cur={'depth':s.depth,'cells':[]}; return
        if s.cur is not None and s.cell is None and s.depth==s.cur['depth']+1:
            s.cell={'text':'','href':a.get('href'),'cls':a.get('class') or '','title':a.get('title')}
        elif s.cell is not None and tag=='a' and not s.cell['href']: s.cell['href']=a.get('href')
        if s.cell is not None and tag=='img' and a.get('title') and not s.cell['title']: s.cell['title']=a.get('title')
    def handle_endtag(s,tag):
        if s.cell is not None and s.depth==s.cur['depth']+1:
            s.cur['cells'].append(s.cell); s.cell=None
        if s.cur is not None and s.depth==s.cur['depth']:
            s.cur['section']=s.heads[-1].strip() if s.heads else ''
            s.rows.append(s.cur); s.cur=None
        if s.inhead==s.depth: s.inhead=None
        s.depth-=1
    def handle_startendtag(s,tag,a):
        a=dict(a)
        if s.cell is not None and tag=='img' and a.get('title') and not s.cell['title']: s.cell['title']=a.get('title')
    def handle_data(s,d):
        if s.cell is not None: s.cell['text']+=d
        if s.inhead: s.heads[-1]+=d
VOID={'img','br','input','meta','link','source','hr','col','wbr'}
class P2(P):
    def handle_starttag(s,tag,a):
        P.handle_starttag(s,tag,a)
        if tag in VOID: P.handle_startendtag(s,tag,a); s.depth-=1

def parse(f, national):
    t=open(f,encoding='utf-8',errors='replace').read()
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S)
    p=P2(); p.feed(t)
    out=[]; sect=None
    for r in p.rows:
        c=[x['text'].strip() for x in r['cells']]
        nonempty=[x for x in c if x]
        di=next((i for i,x in enumerate(c) if re.fullmatch(r'\d\d/\d\d/\d\d',x)),None)
        if di is None:
            if len(nonempty)==1: sect=nonempty[0]
            continue
        ri=next((i for i,x in enumerate(r['cells']) if x['href'] and 'spielbericht' in x['href']),None)
        if ri is None: continue
        sec=r['section'] if r['section'] and r['section']!='' and not national else sect
        out.append(dict(section=sec,md=c[0],date=c[di],home=c[ri-2],away=c[ri-1],result=c[ri],pos=c[ri+1],goals=c[ri+2] if len(c)>ri+2 else '',
            assists=c[ri+3] if len(c)>ri+3 else '',report=r['cells'][ri]['href'].split('/')[-1]))

    return out

SEASONS = range(2004, 2021)  # 2004/05 to 2020/21
SAVE_HELP = ('Open the page in a browser, scroll down until the table of matches appears, '
             'then save it with "Save Page As > Webpage, Complete".')

def fail(lines):
    print('\nERROR: Transfermarkt stats pages are unusable:', file=sys.stderr)
    for line in lines:
        print('  - ' + line, file=sys.stderr)
    print('\n' + SAVE_HELP, file=sys.stderr)
    sys.exit(1)

found, empty, empty_keys = {}, [], set()
for f in sorted(glob.glob(RAW + '*.html')):
    head = open(f, encoding='utf-8', errors='replace').read(20000)
    url = re.search(r'og:url" content="([^"]*)"', head)
    if not url:
        continue
    url = url.group(1)
    if '/nationalmannschaft/' in url:
        key, name, national = 'national team', 'tm_arg.json', True
    elif '/leistungsdatendetails/' in url and re.search(r'/saison/(\d{4})', url):
        year = int(re.search(r'/saison/(\d{4})', url).group(1))
        key, name, national = year, 'club_%d.json' % year, False
    else:
        continue
    rows = parse(f, national)
    if not rows:
        # The stats table is filled in by the page's scripts only after scrolling;
        # a page saved before that holds the page frame and no match rows.
        empty.append('%s (%s): the stats table has no match rows; the page was saved before the table loaded'
                     % (os.path.basename(f), url))
        empty_keys.add(key)
        continue
    found[key] = (name, rows)

missing = ['season %d/%02d: no saved stats page' % (y, (y + 1) % 100) for y in SEASONS if y not in found and y not in empty_keys]
if 'national team' not in found and 'national team' not in empty_keys:
    missing.append('national team page: not found')
if empty or missing:
    fail(empty + missing)

for key, (name, rows) in found.items():
    json.dump(rows, open(WORK + 'tm/' + name, 'w'), indent=0, ensure_ascii=False)
    print(name, len(rows), 'matches')
print(len(found), 'stats pages parsed')

"""Parse Transfermarkt's "All goals" page (detailed view) for Messi.

The page is server-rendered, so a plain browser save keeps its table. Each match is
one full row; further goals in the same match follow as short rows that inherit the
match details. Returns one dict per goal with the minute, score at the time
(home:away as Transfermarkt prints it), type of goal and assister.
"""
import sys,re,html,json,datetime
def cl(s): return html.unescape(re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',s))).strip()
def parse(path):
    t=open(path,encoding='utf-8',errors='replace').read()
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S)
    tb=max(re.findall(r'<table.*?</table>',t,re.S),key=len)
    out=[]; cur=None
    for r in re.findall(r'<tr[^>]*>(.*?)</tr>',tb,re.S):
        tds=re.findall(r'<td[^>]*>(.*?)</td>',r,re.S)
        c=[cl(x) for x in tds]
        if len(c)>=14 and re.fullmatch(r'\d{1,2}/\d{1,2}/\d{2}',c[3]):
            team=re.search(r'title="([^"]*)"',tds[5]) or re.search(r'alt="([^"]*)"',tds[5])
            cur=dict(comp=c[1],date=datetime.datetime.strptime(c[3],'%m/%d/%y').strftime('%Y-%m-%d'),venue=c[4],
                     team=team.group(1) if team else c[5],opp=c[7],result=c[8])
            g=c[10:14]
        elif len(c)==5 and cur and re.search(r"\d'",c[1]):
            g=c[1:5]
        else: continue
        out.append(dict(cur,minute=g[0].replace("'",'').replace(' ',''),at_score=g[1],type=g[2],assist=g[3] or None))
    return out

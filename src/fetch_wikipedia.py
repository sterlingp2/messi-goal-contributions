"""Download the Wikipedia pages the pipeline parses, pinned to fixed revisions.

Wikipedia supplies Argentina final scores, home/away/neutral venues and the minute of
each competitive Argentina goal. Pages are fetched as raw wikitext, one at a time with a
pause between requests, to stay inside Wikimedia's rate limits.
"""
import json, os, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import WORK

UA = {'User-Agent': 'messi-goal-contributions/1.0 (dataset build script)'}
HERE = os.path.dirname(os.path.abspath(__file__))
revs = json.load(open(os.path.join(HERE, 'wiki_revisions.json'), encoding='utf-8'))

def target(title):
    if title.startswith('List of international goals'):
        return 'raw.txt'
    if title == 'Argentina national football team results (2000–2019)':
        return 'res0019.txt'
    if title == 'Argentina national football team results (2020–present)':
        return 'Argentina_national_football_team_results_2020-present.txt'
    return 't_' + ''.join(c for c in title if c.isalnum() or c == ' ').replace(' ', '_') + '.txt'

for title, rev in revs.items():
    path = WORK + 'wiki/' + target(title)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        continue
    url = f'https://en.wikipedia.org/w/index.php?oldid={rev}&action=raw'
    for attempt in range(5):
        try:
            text = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode('utf-8')
            open(path, 'w', encoding='utf-8').write(text)
            print('fetched', title, rev)
            break
        except Exception as e:
            print('retrying', title, e)
            time.sleep(15 * (attempt + 1))
    else:
        sys.exit('could not fetch ' + title)
    time.sleep(3)

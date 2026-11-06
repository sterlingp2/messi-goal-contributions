"""Paths shared by every pipeline step. Override with environment variables."""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(os.environ.get('MESSI_WORKDIR', os.path.join(ROOT, 'work')), '')
RAW = os.path.join(os.environ.get('MESSI_RAW', os.path.join(ROOT, 'raw', 'transfermarkt')), '')
OUT = os.path.join(ROOT, 'data', '')
CUTOFF = '2021-05-16'  # Messi's last Barcelona match
for d in (WORK, OUT, WORK + 'sb', WORK + 'wiki', WORK + 'tm', WORK + 'ext'):
    os.makedirs(d, exist_ok=True)

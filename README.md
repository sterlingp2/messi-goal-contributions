# Lionel Messi goal contributions, 2004–2021

Every goal and assist Lionel Messi recorded in official matches for FC Barcelona and in senior matches for Argentina, from his Barcelona debut (16 October 2004) to his last Barcelona match (16 May 2021). One row per contribution: 1,089 rows.

| | Goals | Assists |
|---|---:|---:|
| Barcelona, La Liga | 474 | 216 |
| Barcelona, Champions League, Copa del Rey, Supercopa, UEFA Super Cup, Club World Cup | 198 | 87 |
| Argentina (friendlies, World Cup qualifiers, World Cup, Copa América) | 71 | 43 |
| **Total** | **743** | **346** |

Every match's goal and assist count agrees with Transfermarkt.

**Interactive dashboard:** https://claude.ai/artifact/RRWasdybTgoi88fiqQ3m9h — filter by competition, season, opponent, teammate, body part or situation; see every contribution on a pitch map; and browse the full table.

Files: [`data/messi_contributions.csv`](data/messi_contributions.csv) and [`data/messi_contributions.json`](data/messi_contributions.json) hold the same rows.

## Columns

| Column | Meaning |
|---|---|
| `id` | Row number, in date order |
| `date` | Local match date, `YYYY-MM-DD` |
| `season` | Season, July to June (`2010/11`); Argentina matches use the same split |
| `kind` | `Goal` (Messi scored) or `Assist` (Messi assisted a teammate) |
| `team` | `Barcelona` or `Argentina` |
| `comp` | Competition |
| `opp` | Opponent |
| `venue` | `H` home, `A` away, `N` neutral |
| `score` | Final score, Messi's team first (`3–1`) |
| `result` | `W`, `D` or `L` for Messi's team |
| `minute` | Minute of the goal; stoppage time as `45+2`. Empty for 21 Argentina friendly goals |
| `body` | Body part of the finish: `Left Foot`, `Right Foot`, `Head`, `Other`. For assists, the teammate's finish |
| `gtype` | `Open Play`, `Penalty` or `Free Kick` (direct) |
| `technique` | Finishing technique where StatsBomb or the video log records one (`Lob`, `Volley`, `tap-in`) |
| `partner` | For a goal, the teammate credited with the assist (empty if none). For an assist, the teammate who scored |
| `assist_type` | Assists only: `Pass`, `Cross`, `Corner`, `Free kick`, `Shot on goal` (teammate scored the rebound of a Messi shot) or `Won penalty` |
| `x`, `y` | Where the ball was struck. `x` 0–100 toward the opponent's goal, `y` 0–100 across the pitch with 0 on the attacker's left. For assists, the teammate's shot |
| `px`, `py` | Assists with tracked data only: where Messi's pass or shot started |
| `xg` | StatsBomb expected goals of the shot, where tracked |
| `locsrc` | Source of `x`/`y`: `statsbomb` (event data), `video` (hand-placed from match footage) or empty |

## Definitions

- **Assist** follows Transfermarkt's definition in every competition, so totals match the figures usually quoted: a pass, cross or set piece leading directly to a goal; a rebound from a Messi shot; or a penalty Messi won that a teammate scored. A penalty Messi won and scored himself is not an assist.
- **Scope** is official matches only. Club friendlies (for example the Joan Gamper Trophy) and youth tournaments (2005 U-20 World Cup, 2008 Olympics) are excluded.
- **Pitch locations** exist for every goal and for every La Liga assist. The 141 assists in other competitions have no location, because no tracking data exists for those matches.

## Sources and credits

- **StatsBomb open data** (https://github.com/statsbomb/open-data): every La Liga match Messi played from 2004/05 to 2020/21, the 2009, 2011 and 2015 Champions League finals, and the 2018 World Cup. Supplies shot and pass coordinates, body part, xG and most La Liga assists. Data provided by StatsBomb; use is subject to StatsBomb's open data terms in that repository.
- **Transfermarkt** (https://www.transfermarkt.com): per-match goal and assist counts for every season and for Argentina, and from match reports the scorer, minute and assist type of each assist that StatsBomb does not cover. The pages were saved by hand from a browser. **The raw Transfermarkt pages are not redistributed in this repository**; only facts extracted from them (who assisted whom, when, in which match) appear in `data/`. This project is not affiliated with Transfermarkt.
- **Wikipedia** (English): Argentina final scores, home/away/neutral venues, and the minute of every competitive Argentina goal, from the list of Messi's international goals and the tournament match records.
- **Club goal log** derived from Transfermarkt by [avishek-choudhary/Lionel-Messi-Club-Career-Goals-Analysis](https://github.com/avishek-choudhary/Lionel-Messi-Club-Career-Goals-Analysis): minute, final score and assister of each Barcelona goal.
- **Video-transcribed goal log** by [raym26/messi-800-goals-dataset](https://github.com/raym26/messi-800-goals-dataset): location and body part of goals outside StatsBomb's coverage.

## How the sources were merged

- Goals start from the club goal log and the video log, matched by date and order within the match; StatsBomb replaces location, body part and xG wherever it covers the match. The video log's locations agree with StatsBomb's to within about 1% of the pitch on the 459 goals both cover.
- Argentina dates follow the local match date. The video log was often one day late, and once 11 days off.
- In La Liga, Transfermarkt credits 30 more assists than StatsBomb's `goal_assist` flag. 19 were found in StatsBomb's event data: in each of those matches the number of teammate goals that came straight from a Messi pass, or from the rebound of a Messi shot, equals Transfermarkt's extra count exactly. The remaining 12 came from Transfermarkt's match reports for 11 matches, which also removed one StatsBomb assist Transfermarkt does not credit (19 + 12 − 1 = 30).
- Penalty goals carry no assister. Teammate and opponent names are unified across sources.

## Data and licensing

**The MIT license in [`LICENSE`](LICENSE) covers the code only** (`src/`, `run.sh`). The files in `data/` are not licensed by this repository: they are facts compiled from the sources above, and any reuse is subject to those sources' own terms, including StatsBomb's attribution requirement. If you publish work built on `data/`, credit StatsBomb and Transfermarkt.

## Rebuilding the data

Requires Python 3.9+ and git; no third-party Python packages.

1. Save the Transfermarkt pages listed below from a browser (**Save Page As → Webpage, HTML only**) into `raw/transfermarkt/`. That folder is git-ignored and must never be committed.
   - Messi's detailed stats page for each season, 2004/05 to 2020/21: `https://www.transfermarkt.com/lionel-messi/leistungsdatendetails/spieler/28003/saison/YEAR/plus/1` with `YEAR` = 2004 … 2020.
   - Messi's national-team page, detailed view: `https://www.transfermarkt.com/lionel-messi/nationalmannschaft/spieler/28003/verein/3437/plus/1`.
   - The match report of every match outside La Liga in which he has an assist, and of the La Liga matches the build reports as unresolved. Report links are on the stats pages (click the score).
2. Run `./run.sh`. It downloads StatsBomb data, the pinned Wikipedia revisions and the two goal logs into `work/` (also git-ignored), then writes `data/`.

The build prints a reconciliation summary; any La Liga match it cannot settle from StatsBomb's events is listed as unresolved and needs its match report.

## Known gaps

- No pitch location for the 141 assists outside La Liga.
- No minute for 21 Argentina friendly goals.

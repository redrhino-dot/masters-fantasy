#!/usr/bin/env python3
import requests, json, re, unicodedata, sys
from datetime import datetime

ESPN_URL = "https://www.espn.com/golf/leaderboard/_/tournamentId/401811941"

TEAM_PLAYERS = [
    'Xander Schauffele', 'Tommy Fleetwood', 'Harris English', 'Charl Schwartzel',
    'Jon Rahm', 'Tyrrell Hatton', 'Cameron Smith', 'Dustin Johnson',
    'Matt Fitzpatrick', 'JJ Spaun', 'Aaron Rai',
    'Cameron Young', 'Marco Penge', 'Samuel Stevens',
    'Bryson DeChambeau', 'Chris Gotterup', 'Sergio Garcia'
]

ALIASES = {
    'j.j. spaun':        'JJ Spaun',
    'jj spaun':          'JJ Spaun',
    'sam stevens':       'Samuel Stevens',
    'sergio garcia':     'Sergio Garcia',
    'sergio garc\u00eda': 'Sergio Garcia',
    'bryson dechambeau': 'Bryson DeChambeau',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Referer': 'https://www.espn.com/golf/',
}

def normalize(s):
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).strip()

def clean(s):
    return normalize(s).lower().replace('.','').replace('-',' ').replace('\u00a0',' ').strip()

def resolve(espn_name):
    k = clean(espn_name)
    if k in ALIASES:
        return ALIASES[k]
    for p in TEAM_PLAYERS:
        if clean(p) == k:
            return p
    return None

def parse_pos(t):
    t = t.strip().upper()
    if t in ('CUT','MC','WD','DQ','MDF','DNF','RTD','W/D'):
        return None, True
    m = re.match(r'T?(\d+)', t)
    return (int(m.group(1)), False) if m else (None, False)

def parse(html):
    # Pure regex — no BeautifulSoup needed
    # Matches: position in "tl TableTD" cell, then player name in leaderboardplayername anchor
    pattern = re.compile(
        r'<td class="tl TableTD">([^<]+)</td>'
        r'[\s\S]{0,600}?'
        r'leaderboardplayername[^>]+>([^<]+)</a>'
    )
    scores = {}
    for m in pattern.finditer(html):
        pos_text = m.group(1).strip()
        name_raw = m.group(2).strip()
        our = resolve(name_raw)
        if our:
            pos, cut = parse_pos(pos_text)
            scores[our] = {'position': pos, 'cut': cut, 'live': False}

    current_round = 'R1'
    for n in ['4', '3', '2', '1']:
        if f'Round {n}' in html:
            current_round = f'R{n}'
            break

    return scores, current_round

if __name__ == '__main__':
    try:
        print(f"[{datetime.utcnow().strftime('%H:%M UTC')}] Fetching ESPN leaderboard...")
        resp = requests.get(ESPN_URL, headers=HEADERS, timeout=25)
        resp.raise_for_status()
        html = resp.text
        print(f"  {len(html):,} bytes | HTTP {resp.status_code}")

        with open('debug_espn.html', 'w', encoding='utf-8') as f:
            f.write(html)

        scores, rnd = parse(html)
        matched = len(scores)
        missing = [p for p in TEAM_PLAYERS if p not in scores]

        print(f"  Matched {matched}/{len(TEAM_PLAYERS)}")
        if missing:
            print(f"  Missing: {missing}")

        if matched == 0:
            print("  No players matched — check debug_espn.html artifact")
            sys.exit(1)

        result = {
            'currentRound': rnd,
            'lastUpdated': datetime.utcnow().strftime('%H:%M UTC'),
            'source': 'ESPN HTML',
            'players': scores,
        }
        with open('scores.json', 'w') as f:
            json.dump(result, f, indent=2)
        print(f"✓ scores.json updated — {rnd} — {matched} players")

    except Exception as e:
        print(f"✗ Fatal: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

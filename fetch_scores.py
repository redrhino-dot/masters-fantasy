#!/usr/bin/env python3
import requests, json, re, sys
from datetime import datetime

ESPN_URL = "https://www.espn.com/golf/leaderboard/_/tournamentId/401811941"

TEAM_PLAYERS = [
    'Xander Schauffele', 'Tommy Fleetwood', 'Harris English', 'Charl Schwartzel',
    'Jon Rahm', 'Tyrrell Hatton', 'Cameron Smith', 'Dustin Johnson',
    'Matt Fitzpatrick', 'JJ Spaun', 'Aaron Rai',
    'Cameron Young', 'Marco Penge', 'Samuel Stevens',
    'Bryson DeChambeau', 'Chris Gotterup', 'Sergio Garcia'
]

SLUG_MAP = {
    'xander-schauffele':  'Xander Schauffele',
    'tommy-fleetwood':    'Tommy Fleetwood',
    'harris-english':     'Harris English',
    'charl-schwartzel':   'Charl Schwartzel',
    'jon-rahm':           'Jon Rahm',
    'tyrrell-hatton':     'Tyrrell Hatton',
    'cameron-smith':      'Cameron Smith',
    'dustin-johnson':     'Dustin Johnson',
    'matt-fitzpatrick':   'Matt Fitzpatrick',
    'jj-spaun':           'JJ Spaun',
    'aaron-rai':          'Aaron Rai',
    'cameron-young':      'Cameron Young',
    'marco-penge':        'Marco Penge',
    'sam-stevens':        'Samuel Stevens',
    'samuel-stevens':     'Samuel Stevens',
    'bryson-dechambeau':  'Bryson DeChambeau',
    'chris-gotterup':     'Chris Gotterup',
    'sergio-garcia':      'Sergio Garcia',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Referer': 'https://www.espn.com/golf/',
}

def parse_pos(t):
    t = t.strip().upper()
    if t in ('CUT','MC','WD','DQ','MDF','DNF','RTD'):
        return None, True
    m = re.match(r'T?(\d+)', t)
    return (int(m.group(1)), False) if m else (None, False)

def parse(html):
    scores = {}
    for slug, our_name in SLUG_MAP.items():
        if our_name in scores:
            continue
        # Direct string search — works regardless of URL format
        idx = html.find(f'/{slug}')
        if idx == -1:
            continue
        # Look backward up to 1500 chars for a position value
        before = html[max(0, idx - 1500):idx]
        pos_hits = re.findall(r'>[ \t]*(T?\d+|CUT|MC|WD|DQ|MDF|DNF)[ \t]*<', before)
        pos_text = pos_hits[-1] if pos_hits else None
        pos, cut = parse_pos(pos_text) if pos_text else (None, False)
        scores[our_name] = {'position': pos, 'cut': cut, 'live': False}
        print(f"  {our_name:<22} slug={slug:<25} pos={pos_text}")

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
            print("  No players matched.")
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

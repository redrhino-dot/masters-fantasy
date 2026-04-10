#!/usr/bin/env python3
"""
Masters 2026 Fantasy - Score Fetcher
Parses ESPN leaderboard HTML using the exact structure confirmed from debug_espn.html.
"""
import requests, json, re, unicodedata, sys
from datetime import datetime
from bs4 import BeautifulSoup

ESPN_URL = "https://www.espn.com/golf/leaderboard/_/tournamentId/401811941"

TEAM_PLAYERS = [
    'Xander Schauffele', 'Tommy Fleetwood', 'Harris English', 'Charl Schwartzel',
    'Jon Rahm', 'Tyrrell Hatton', 'Cameron Smith', 'Dustin Johnson',
    'Matt Fitzpatrick', 'JJ Spaun', 'Aaron Rai',
    'Cameron Young', 'Marco Penge', 'Samuel Stevens',
    'Bryson DeChambeau', 'Chris Gotterup', 'Sergio Garcia'
]

# ESPN uses different name formats — map them here
ESPN_ALIASES = {
    'j.j. spaun':         'JJ Spaun',
    'jj spaun':           'JJ Spaun',
    'sam stevens':        'Samuel Stevens',
    'sergio garcia':      'Sergio Garcia',
    'sergio garcía':      'Sergio Garcia',
    'bryson dechambeau':  'Bryson DeChambeau',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Referer': 'https://www.espn.com/golf/',
}

def normalize(s):
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).strip()

def canonical(name):
    return normalize(name).lower().replace('.', '').replace('-', ' ').strip()

def resolve_name(espn_name):
    key = canonical(espn_name)
    if key in ESPN_ALIASES:
        return ESPN_ALIASES[key]
    for p in TEAM_PLAYERS:
        if canonical(p) == key:
            return p
    return None

def parse_pos(text):
    t = text.strip().upper()
    if t in ('CUT', 'MC', 'WD', 'DQ', 'MDF', 'DNF', 'RTD', 'W/D'):
        return None, True
    m = re.match(r'T?(\d+)', t)
    return (int(m.group(1)), False) if m else (None, False)

def detect_round(soup):
    text = soup.get_text()
    for n in ['4', '3', '2', '1']:
        if f'Round {n}' in text:
            return f'R{n}'
    return 'R1'

def parse_leaderboard(html):
    soup = BeautifulSoup(html, 'html.parser')
    scores = {}
    current_round = detect_round(soup)

    # Each player has an anchor with class "leaderboardplayername" — confirmed in debug_espn.html
    player_anchors = soup.find_all('a', class_=lambda c: c and 'leaderboardplayername' in c)
    print(f"  Player anchors found: {len(player_anchors)}")

    for anchor in player_anchors:
        espn_name = anchor.get_text(strip=True)
        our_name = resolve_name(espn_name)
        if not our_name:
            continue

        row = anchor.find_parent('tr')
        if not row:
            continue

        cells = row.find_all('td')
        # Cell[0] = caret icon, Cell[1] = position, Cell[2] = flag + player name
        if len(cells) < 3:
            continue

        pos_text = cells[1].get_text(strip=True)
        pos, cut = parse_pos(pos_text)

        to_par = cells[3].get_text(strip=True) if len(cells) > 3 else '--'
        r1     = cells[6].get_text(strip=True) if len(cells) > 6 else '--'

        scores[our_name] = {
            'position': pos,
            'cut':      cut,
            'live':     False,
            'toPar':    to_par,
            'r1':       r1,
        }

    return scores, current_round

def fetch_scores():
    print(f"[{datetime.utcnow().strftime('%H:%M UTC')}] Fetching ESPN leaderboard...")
    resp = requests.get(ESPN_URL, headers=HEADERS, timeout=25)
    resp.raise_for_status()
    html = resp.text
    print(f"  Received {len(html):,} bytes | HTTP {resp.status_code}")

    with open('debug_espn.html', 'w', encoding='utf-8') as f:
        f.write(html)

    scores, current_round = parse_leaderboard(html)

    matched = len(scores)
    missing = [p for p in TEAM_PLAYERS if p not in scores]
    cut_list = [p for p, v in scores.items() if v['cut']]

    print(f"  Matched {matched}/{len(TEAM_PLAYERS)} players")
    if missing:
        print(f"  Not matched: {missing}")
    if cut_list:
        print(f"  Cut: {cut_list}")

    if matched == 0:
        print("  No players found — check debug_espn.html artifact")
        return None

    return {
        'currentRound': current_round,
        'lastUpdated':  datetime.utcnow().strftime('%H:%M UTC'),
        'source':       'ESPN HTML',
        'players':      scores,
    }

if __name__ == '__main__':
    try:
        result = fetch_scores()
        if result and result['players']:
            with open('scores.json', 'w') as f:
                json.dump(result, f, indent=2)
            print(f"✓ scores.json updated — {result['lastUpdated']} — {len(result['players'])} players")
        else:
            print("✗ scores.json NOT updated.")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Fatal: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

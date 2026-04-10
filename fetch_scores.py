#!/usr/bin/env python3
"""
Masters 2026 Fantasy - Score Fetcher (ESPN HTML parser)
Reads the public ESPN leaderboard page — no hidden API needed.
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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Referer': 'https://www.espn.com/golf/',
}

def normalize(s):
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).strip()

def names_match(a, b):
    def clean(s): return normalize(s).lower().replace('.','').replace('-',' ').strip()
    return clean(a) == clean(b)

def find_player(name):
    for p in TEAM_PLAYERS:
        if names_match(name, p):
            return p
    return None

def parse_pos(text):
    t = text.strip().upper()
    if t in ('CUT','MC','WD','DQ','MDF','DNF','RTD'):
        return None, True
    m = re.match(r'T?(\d+)', t)
    return (int(m.group(1)), False) if m else (None, False)

def detect_round(soup):
    text = soup.get_text()
    for n in ['4','3','2','1']:
        if f'Round {n}' in text or f'ROUND {n}' in text:
            return f'R{n}'
    return 'R1'

# Method A: HTML table rows
def try_table_parse(soup):
    scores = {}
    rows = soup.find_all('tr', class_=lambda c: c and 'Table__TR' in ' '.join(c))
    print(f"  Table rows found: {len(rows)}")
    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 3:
            continue
        pos_text = cells[0].get_text(strip=True)
        if not pos_text or pos_text in ('', 'POS', 'PLAYER'):
            continue
        for cell in cells:
            candidates = [cell.get_text(strip=True)] + [a.get_text(strip=True) for a in cell.find_all('a')]
            for cand in candidates:
                our = find_player(cand)
                if our:
                    pos, cut = parse_pos(pos_text)
                    scores[our] = {'position': pos, 'cut': cut, 'live': False}
                    break
    return scores

# Method B: regex scan over raw HTML
def try_regex_parse(html):
    scores = {}
    for player in TEAM_PLAYERS:
        last = player.split()[-1]
        pattern = rf'(T?\d+|CUT|WD|DQ|MC).{{0,300}}?{re.escape(last)}'
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            pos, cut = parse_pos(m.group(1))
            scores[player] = {'position': pos, 'cut': cut, 'live': False}
    return scores

# Method C: embedded JSON islands in script tags
def try_json_island(soup):
    scores = {}
    for script in soup.find_all('script'):
        src = script.string or ''
        if 'displayName' not in src:
            continue
        pairs = re.findall(r'"displayName":"([^"]+)"[^}]{0,400}?"sortOrder":(\d+)', src)
        for name, order in pairs:
            our = find_player(name)
            if our:
                scores[our] = {'position': int(order), 'cut': False, 'live': False}
        if scores:
            return scores
    return scores

def fetch_scores():
    print(f"[{datetime.utcnow().strftime('%H:%M UTC')}] Fetching ESPN leaderboard page...")
    resp = requests.get(ESPN_URL, headers=HEADERS, timeout=25)
    resp.raise_for_status()
    html = resp.text
    print(f"  Received {len(html):,} bytes  |  HTTP {resp.status_code}")

    with open('debug_espn.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("  debug_espn.html saved")

    soup = BeautifulSoup(html, 'html.parser')
    current_round = detect_round(soup)
    print(f"  Detected round: {current_round}")

    scores = try_table_parse(soup)
    if len(scores) >= 3:
        print(f"  Method A (table): {len(scores)} players matched")
    else:
        print(f"  Method A: {len(scores)} — trying Method B (regex)...")
        scores = try_regex_parse(html)
        if len(scores) >= 3:
            print(f"  Method B (regex): {len(scores)} players matched")
        else:
            print(f"  Method B: {len(scores)} — trying Method C (JSON island)...")
            scores = try_json_island(soup)
            print(f"  Method C (JSON island): {len(scores)} players matched")

    if not scores:
        print("  All methods failed. Check debug_espn.html artifact in Actions.")
        return None

    missing = [p for p in TEAM_PLAYERS if p not in scores]
    if missing:
        print(f"  Not matched: {missing}")

    cut_count = sum(1 for p in scores.values() if p['cut'])
    non_cut = [p for p in scores.values() if not p['cut'] and p['position']]
    cut_line = len(non_cut) if cut_count > 0 else None

    return {
        'currentRound': current_round,
        'lastUpdated': datetime.utcnow().strftime('%H:%M UTC'),
        'source': 'ESPN HTML',
        'cutLine': cut_line,
        'players': scores
    }

if __name__ == '__main__':
    try:
        result = fetch_scores()
        if result and result['players']:
            with open('scores.json', 'w') as f:
                json.dump(result, f, indent=2)
            print(f"✓ scores.json updated — {result['lastUpdated']} — {len(result['players'])} players")
        else:
            print("✗ No scores parsed. scores.json not updated.")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Fatal: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

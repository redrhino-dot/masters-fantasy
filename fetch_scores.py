#!/usr/bin/env python3
import requests, json, re, sys
from datetime import datetime, timezone, timedelta

ESPN_URL = "https://www.espn.com/golf/leaderboard/_/tournamentId/401811941"
BST = timezone(timedelta(hours=1))

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

def strip_tags(s):
    return re.sub(r'<[^>]+>', '', s).strip()

def parse_pos(t):
    t = t.strip().upper()
    if t in ('CUT','MC','WD','DQ','MDF','DNF','RTD'):
        return None, True
    m = re.match(r'T?(\d+)', t)
    return (int(m.group(1)), False) if m else (None, False)

def get_row(html, idx):
    """Return all td text values from the <tr> that contains position idx."""
    tr_start = html.rfind('<tr', 0, idx)
    tr_end   = html.find('</tr>', idx)
    if tr_start == -1:
        return []
    row = html[tr_start : tr_end + 5 if tr_end != -1 else idx + 4000]
    tds = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
    return [strip_tags(td) for td in tds]

def detect_round(html):
    m = re.search(r'Round (\d)\s*[-–]\s*(?:Play|In Progress|Suspended|Complete|Tee)', html)
    if m:
        return f'R{m.group(1)}'
    m = re.search(r'Round (\d) -', html)
    if m:
        return f'R{m.group(1)}'
    return 'R1'

def parse(html):
    scores = {}

    for slug, our_name in SLUG_MAP.items():
        if our_name in scores:
            continue
        idx = html.find(f'/{slug}')
        if idx == -1:
            continue

        # Get all <td> values for this player's row
        tds = get_row(html, idx)
        if not tds:
            continue

        # First non-empty td is ALWAYS the overall tournament position
        pos_text = next((t for t in tds if t and t != ' '), None)
        pos, cut = parse_pos(pos_text) if pos_text else (None, False)

        # Cells after the anchor: toPar, today, thru, R1, R2, R3, R4
        anchor_end = html.find('</a>', idx)
        after = html[anchor_end if anchor_end != -1 else idx : ]
        row_end = after.find('</tr>')
        after_segment = after[:row_end] if row_end != -1 else after[:3000]
        after_tds = [strip_tags(td) for td in re.findall(r'<td[^>]*>(.*?)</td>', after_segment, re.DOTALL)]

        def cell(i): return after_tds[i] if i < len(after_tds) else '--'

        to_par = cell(0)
        r1 = cell(3); r2 = cell(4); r3 = cell(5); r4 = cell(6)

        scores[our_name] = {
            'position': pos, 'cut': cut, 'live': False,
            'toPar': to_par, 'r1': r1, 'r2': r2, 'r3': r3, 'r4': r4,
        }
        print(f"  {our_name:<22} pos={str(pos_text):<6} toPar={to_par:<5} R1={r1} R2={r2} R3={r3} R4={r4}")

    return scores, detect_round(html)

if __name__ == '__main__':
    try:
        now_bst = datetime.now(BST).strftime('%H:%M BST')
        print(f"[{now_bst}] Fetching ESPN leaderboard...")
        resp = requests.get(ESPN_URL, headers=HEADERS, timeout=25)
        resp.raise_for_status()
        html = resp.text
        print(f"  {len(html):,} bytes | HTTP {resp.status_code}")

        with open('debug_espn.html', 'w', encoding='utf-8') as f:
            f.write(html)

        scores, rnd = parse(html)
        matched = len(scores)
        missing = [p for p in TEAM_PLAYERS if p not in scores]
        print(f"  Round detected: {rnd}")
        print(f"  Matched {matched}/{len(TEAM_PLAYERS)}")
        if missing:
            print(f"  Missing: {missing}")

        if matched == 0:
            print("  No players matched.")
            sys.exit(1)

        result = {
            'currentRound': rnd,
            'lastUpdated':  datetime.now(BST).strftime('%H:%M BST'),
            'source':       'ESPN HTML',
            'players':      scores,
        }
        with open('scores.json', 'w') as f:
            json.dump(result, f, indent=2)
        print(f"✓ scores.json updated — {rnd} — {matched} players")

    except Exception as e:
        print(f"✗ Fatal: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

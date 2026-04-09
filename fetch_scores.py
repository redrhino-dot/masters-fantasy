#!/usr/bin/env python3
"""
Masters 2026 Fantasy - Live Score Fetcher
Fetches ESPN leaderboard and writes scores.json for the GitHub Pages site.
"""
import requests, json, unicodedata
from datetime import datetime

EVENT_ID = "401811941"  # Masters 2026
ESPN_URL = f"https://site.web.api.espn.com/apis/site/v2/sports/golf/pga/leaderboard?event={EVENT_ID}"

# All players across the five fantasy teams
TEAM_PLAYERS = [
    'Xander Schauffele', 'Tommy Fleetwood', 'Harris English', 'Charl Schwartzel',
    'Jon Rahm', 'Tyrrell Hatton', 'Cameron Smith', 'Dustin Johnson',
    'Matt Fitzpatrick', 'JJ Spaun', 'Aaron Rai',
    'Cameron Young', 'Marco Penge', 'Samuel Stevens',
    'Bryson DeChambeau', 'Chris Gotterup', 'Sergio Garcia'
]

def normalize(s):
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).strip()

def names_match(api_name, our_name):
    a = normalize(api_name).lower().replace('.', '').replace('  ', ' ')
    b = normalize(our_name).lower().replace('.', '').replace('  ', ' ')
    return a == b

def fetch_scores():
    try:
        resp = requests.get(
            ESPN_URL,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; MastersFantasy/1.0)'},
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"ERROR fetching ESPN API: {e}")
        return None

    event = data.get('events', [{}])[0]
    competition = event.get('competitions', [{}])[0]
    competitors = competition.get('competitors', [])
    if not competitors:
        print("ERROR: No competitors found in API response")
        return None

    # Determine current round from event status
    current_round = event.get('status', {}).get('period', 1)

    scores = {}
    survivors_after_r2 = 0
    total_after_r2 = 0

    for comp in competitors:
        api_name = comp.get('athlete', {}).get('displayName', '')
        sort_order = comp.get('sortOrder', 999)
        status = comp.get('status', {})
        status_name = status.get('type', {}).get('name', '').lower()
        status_state = status.get('type', {}).get('state', '').lower()

        is_cut = status_name in ('cut', 'wd', 'dq', 'mdf', 'mc')
        is_live = status_state == 'in'

        # Count survivors for cut line calculation
        linescores = comp.get('linescores', [])
        if len(linescores) >= 2:
            total_after_r2 += 1
            if not is_cut:
                survivors_after_r2 += 1

        # Match to our fantasy players
        for our_name in TEAM_PLAYERS:
            if names_match(api_name, our_name):
                scores[our_name] = {
                    'position': int(sort_order) if isinstance(sort_order, (int, float)) and sort_order < 900 else None,
                    'cut': is_cut,
                    'live': is_live
                }
                break

    # Cut line = number of survivors (position of last player to make cut)
    cut_line = survivors_after_r2 if total_after_r2 > 0 else None

    matched = len(scores)
    print(f"Matched {matched}/{len(TEAM_PLAYERS)} fantasy players  |  Round {current_round}  |  Cut line: {cut_line}")

    return {
        'currentRound': f'R{current_round}',
        'lastUpdated': datetime.utcnow().strftime('%H:%M UTC'),
        'source': 'ESPN Live',
        'cutLine': cut_line,
        'players': scores
    }

if __name__ == '__main__':
    print(f"Fetching Masters leaderboard... ({datetime.utcnow().strftime('%H:%M UTC')})")
    result = fetch_scores()
    if result:
        with open('scores.json', 'w') as f:
            json.dump(result, f, indent=2)
        print(f"✓ scores.json updated  —  {result['lastUpdated']}")
    else:
        print("✗ Failed — scores.json not updated")

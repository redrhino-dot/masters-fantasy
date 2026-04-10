#!/usr/bin/env python3
import requests, json, re, sys
from datetime import datetime

ESPN_URL = "https://www.espn.com/golf/leaderboard/_/tournamentId/401811941"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Referer': 'https://www.espn.com/golf/',
}

SLUGS = [
    'xander-schauffele','tommy-fleetwood','harris-english','charl-schwartzel',
    'jon-rahm','tyrrell-hatton','cameron-smith','dustin-johnson',
    'matt-fitzpatrick','jj-spaun','aaron-rai','cameron-young',
    'marco-penge','sam-stevens','bryson-dechambeau','chris-gotterup','sergio-garcia'
]

if __name__ == '__main__':
    print(f"[{datetime.utcnow().strftime('%H:%M UTC')}] Fetching...")
    resp = requests.get(ESPN_URL, headers=HEADERS, timeout=25)
    print(f"  HTTP {resp.status_code} | {len(resp.text):,} bytes")

    html = resp.text

    with open('debug_espn.html', 'w', encoding='utf-8') as f:
        f.write(html)

    # Print first 300 chars so we can see what we actually got
    print(f"\n--- HTML START ---")
    print(repr(html[:300]))
    print(f"--- HTML END ---\n")

    # Check what player slugs are actually present
    print("Slug search results:")
    found_any = False
    for slug in SLUGS:
        if slug in html:
            print(f"  FOUND: {slug}")
            found_any = True
        else:
            print(f"  MISSING: {slug}")

    # Check for key HTML markers
    print(f"\nKey markers:")
    for marker in ['leaderboardplayername', 'golf/player/id', 'golf/player/_', 'TableTD', 'PlayerRow', 'Schauffele']:
        count = html.count(marker)
        print(f"  '{marker}' appears {count} times")

    if not found_any:
        print("\nNo slugs found at all — ESPN may be blocking or returning a different page")
        sys.exit(1)

    print("\nDiagnostic complete — check log above")
    sys.exit(1)  # exit 1 so we can see the output in Actions

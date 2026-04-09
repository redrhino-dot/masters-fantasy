# Masters 2026 Fantasy Tracker 🏌️

Live fantasy leaderboard for the 2026 Masters Tournament.
Auto-updates every 15 minutes via GitHub Actions + ESPN API.

## Setup (5 minutes)

### 1. Create repository
- Go to github.com → New repository → Name: `masters-fantasy`
- Set **Public** → Create repository

### 2. Upload all files
Upload everything in this zip to the root of your repo:
- `index.html`
- `scores.json`
- `fetch_scores.py`
- `.github/workflows/update-scores.yml`
- `README.md`

> ⚠️ The `.github/` folder must be uploaded with its full path intact.
> Use **"uploading an existing file"** on GitHub, or drag the whole folder.

### 3. Enable GitHub Pages
Settings → Pages → Source: **Deploy from branch** → Branch: `main` / `(root)` → Save

Your site is live at: `https://yourusername.github.io/masters-fantasy`

### 4. Enable Actions (if needed)
If Actions are disabled: Actions tab → "I understand my workflows, go ahead and enable them"

## How it works

```
Every 15 min (during tournament):
  GitHub Action → fetch_scores.py → ESPN API
                                  → scores.json (committed to repo)
                                  → GitHub Pages serves updated file
                                  → index.html fetches scores.json (auto-refresh every 5 min)
```

## Teams

| Team | Pick 1 | Pick 2 | Pick 3 | Pick 4 |
|---|---|---|---|---|
| Kris | Schauffele | Fleetwood | English | Schwartzel |
| Graham | Rahm | Hatton | C. Smith | D. Johnson |
| Carey | Rahm | Fitzpatrick | Spaun | Rai |
| Matt | Schauffele | C. Young | Penge | Stevens |
| Patrick | DeChambeau | Fleetwood | Gotterup | Garcia |

**Leagues:** Overall (all 5) · League 1 (Kris/Graham/Carey) · League 2 (Kris/Matt/Patrick)

**Scoring:** Lowest sum of 4 player leaderboard positions wins. Missed cut = cut line position + 1.

## Notes
- The ESPN API used is unofficial and may change without notice
- GitHub Actions free tier: 2,000 mins/month (more than enough for 4 days)
- If the Action fails, the site falls back to the last saved `scores.json`

# Race to 21

A scoreboard for a Premier League sweepstake: everyone picks four players, and
the aim is for their combined 2026/27 league goals to total exactly **21**.

**Live page:** https://samstephenfields.github.io/goals-21/

## How it works

- `data/picks.json` — who picked whom. Players are pinned by their Premier
  League player id, so the tally survives a name spelling change or a transfer.
- `scripts/update.py` — pulls the official Premier League player feed and writes
  `data/standings.json`.
- `index.html` — reads that file and draws the cards.
- `.github/workflows/update.yml` — runs the script every **Sunday at 8pm UK time**
  and commits the result, which republishes the page.

Only Premier League goals count. Own goals are excluded.

## Running it by hand

```
python3 scripts/update.py
```

Or trigger the **Update goals** workflow from the Actions tab.

## Changing a pick

Edit `data/picks.json` — swap the player id in that person's `picks` list and add
a matching entry to `labels`. Player ids come from the same feed the script uses.

# Race to 21

A scoreboard for a Premier League sweepstake: everyone picks four players, and
the aim is for their combined 2026/27 league goals to total exactly **21**.

**Live page:** https://samstephenfields.github.io/goals-21/

## How it works

- `data/picks.json` — who picked whom, plus which club each person supports.
  Players are pinned by their Premier League player id, so the tally survives a
  name spelling change or a transfer.
- `scripts/update.py` — pulls the official Premier League player feed and writes
  `data/standings.json`. It also fetches each scorer's match history so a row can
  show which games the goals came in; players still on nought are skipped, so the
  run costs one call plus one per scorer.
- `index.html` — reads that file and draws the cards.
- `.github/workflows/update.yml` — runs the script every **Sunday at 8pm UK time**
  and commits the result, which republishes the page.

Tapping a player who has scored opens their goals by fixture — gameweek,
opponent, and the final score. It uses `<details>`/`<summary>`, so it works with
a keyboard and a screen reader without extra scripting.

Only Premier League goals count. Own goals are excluded.

## Club crests

Each card is themed to the club its owner supports — a banner gradient in the
club's colours, the club crest as a faint watermark, and the crest again beside
the name.

The images in `crests/` are generated from source artwork by
`scripts/prep_crests.py`, which knocks out the background (flood filling inward
from the edges, so white *inside* a crest survives), trims to the artwork, fits
it to a 240px square and saves a palette PNG. That keeps the whole set to about
55KB. Re-run it only when adding or replacing a club:

```
python3 -m pip install Pillow
python3 scripts/prep_crests.py "/path/to/crest artwork"
```

Club colours and crest paths live in the `clubs` block of `data/picks.json`.

## Running it by hand

```
python3 scripts/update.py
```

Or trigger the **Update goals** workflow from the Actions tab.

## Changing a pick

Edit `data/picks.json` — swap the player id in that person's `picks` list and add
a matching entry to `labels`. Player ids come from the same feed the script uses.

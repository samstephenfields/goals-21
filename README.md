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
- `.github/workflows/update.yml` — runs the script every **Sunday evening** and
  commits the result, which republishes the page.

### About the schedule

The workflow asks for 19:00 and 20:00 UTC on Sundays, but GitHub's shared
scheduler runs queued jobs late — observed delays here are 1-3.5 hours — so in
practice it lands between about 8pm and 11pm UK. That is after the day's
matches, which is what matters for the goal counts.

Two slots are booked so one can be dropped without losing the week. The first
to arrive does the work; the second sees that the data already carries today's
date and stands down. `scripts/check_fresh.py` then runs on every attempt,
including the ones that stand down, and fails the job if the published goals
are more than 8 days old — so a stalled schedule shows up as a failed run
rather than a quiet success.

Tapping a player who has scored opens their goals by fixture — gameweek,
opponent, final score and that match's xG — above a season xG summary saying
whether he's been riding his luck or is due a goal. (Season xG covers every
appearance, so it won't equal the fixtures listed beneath it.) It uses
`<details>`/`<summary>`, so it works with a keyboard and a screen reader without
extra scripting. Team news from the feed shows as an INJ, DOUBT or SUSP flag on
the player's row.

**Now / On pace** switches the table between goals scored and a naive
extrapolation over all 38 gameweeks. It reorders the board, because leading on
goals and being on course for exactly 21 are very different things.

**The season chart** plots each person's cumulative goals gameweek by gameweek
against the target line. The curves are rebuilt from the per-match data on every
run rather than stored, so they cannot drift away from the totals.

Seven series share one chart, and no seven-hue palette clears the colour
separation floors when every line is on screen at once, so each series also
carries its own dash pattern, repeated in the legend. Identity never rests on
hue alone. The palette is slots 1-7 of the reference dark categorical theme,
checked with the data-viz validator against this page's card surface.

`scripts/make_og.py` draws `og.png`, the card WhatsApp shows when the link is
pasted into the group, and rewrites the `og:` block in `index.html`. The image
URL carries the gameweek, because WhatsApp caches a preview per URL and would
otherwise never show a new week.

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

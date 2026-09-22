#!/usr/bin/env python3
"""Rebuild data/standings.json from the official Premier League (FPL) API.

Players are pinned by FPL element id, so results never depend on name spelling
or a player changing clubs mid-season.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

API = "https://fantasy.premierleague.com/api/bootstrap-static/"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PICKS = os.path.join(ROOT, "data", "picks.json")
OUT = os.path.join(ROOT, "data", "standings.json")


def fetch():
    req = urllib.request.Request(API, headers={"User-Agent": "race-to-21/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def previous():
    """Last good standings, used to carry a player over if the API drops them."""
    try:
        with open(OUT) as f:
            prev = json.load(f)
    except (OSError, ValueError):
        return {}
    return {
        str(p["id"]): p
        for person in prev.get("people", [])
        for p in person.get("players", [])
    }


def main():
    picks = json.load(open(PICKS))
    data = fetch()

    teams = {t["id"]: t for t in data["teams"]}
    positions = {p["id"]: p["singular_name_short"] for p in data["element_types"]}
    elements = {p["id"]: p for p in data["elements"]}
    prev = previous()

    finished = [e for e in data["events"] if e.get("finished")]
    current = next((e for e in data["events"] if e.get("is_current")), None)
    played = len(finished)

    missing = []
    people = []
    for person in picks["people"]:
        players = []
        for pid in person["picks"]:
            el = elements.get(pid)
            if el:
                players.append({
                    "id": pid,
                    "name": picks["labels"].get(str(pid), el["web_name"]),
                    "team": teams[el["team"]]["name"],
                    "teamShort": teams[el["team"]]["short_name"],
                    "position": positions[el["element_type"]],
                    "goals": el["goals_scored"],
                    "minutes": el["minutes"],
                    "active": True,
                })
            else:
                # Left the Premier League: freeze their tally at the last known value.
                old = prev.get(str(pid), {})
                missing.append(pid)
                players.append({
                    "id": pid,
                    "name": picks["labels"].get(str(pid), "Unknown"),
                    "team": old.get("team", "—"),
                    "teamShort": old.get("teamShort", "—"),
                    "position": old.get("position", "—"),
                    "goals": old.get("goals", 0),
                    "minutes": old.get("minutes", 0),
                    "active": False,
                })
        total = sum(p["goals"] for p in players)
        players.sort(key=lambda p: -p["goals"])
        club = picks["clubs"].get(person.get("club"), {})
        people.append({
            "name": person["name"],
            "club": person.get("club"),
            "clubName": club.get("name"),
            "clubNick": club.get("nick"),
            "players": players,
            "total": total,
            "remaining": picks["target"] - total,
            "bust": total > picks["target"],
        })

    # Closest to the target first; if level, fewer goals leads (still climbing).
    people.sort(key=lambda p: (abs(p["remaining"]), p["total"]))
    for i, p in enumerate(people):
        p["rank"] = i + 1

    out = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "season": picks["season"],
        "title": picks["title"],
        "rules": picks["rules"],
        "target": picks["target"],
        "gameweek": current["id"] if current else played,
        "gameweeksPlayed": played,
        "source": "Premier League Fantasy API",
        "sourceUrl": API,
        "clubs": picks["clubs"],
        "people": people,
    }
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")

    if missing:
        print("warning: %d pick(s) not in the API, carried over: %s" % (len(missing), missing), file=sys.stderr)
    print("Wrote %s — GW%d, %d gameweeks played" % (OUT, out["gameweek"], played))
    for p in people:
        print("  %d. %-8s %2d goals (%+d vs %d)" % (p["rank"], p["name"], p["total"], -p["remaining"], picks["target"]))


if __name__ == "__main__":
    main()

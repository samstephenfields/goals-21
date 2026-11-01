#!/usr/bin/env python3
"""Rebuild data/standings.json from the official Premier League (FPL) API.

Players are pinned by FPL element id, so results never depend on name spelling
or a player changing clubs mid-season.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

API = "https://fantasy.premierleague.com/api/bootstrap-static/"
PLAYER_API = "https://fantasy.premierleague.com/api/element-summary/%d/"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PICKS = os.path.join(ROOT, "data", "picks.json")
OUT = os.path.join(ROOT, "data", "standings.json")


def get(url, tries=3):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "race-to-21/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except (urllib.error.URLError, ValueError, OSError):
            if attempt == tries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def fetch():
    return get(API)


def scoring_games(pid, teams):
    """Every match this player scored in, newest first."""
    data = get(PLAYER_API % pid)
    games = []
    for g in data.get("history", []):
        if not g.get("goals_scored"):
            continue
        home = g["was_home"]
        hs, as_ = g.get("team_h_score"), g.get("team_a_score")
        for_, against = (hs, as_) if home else (as_, hs)
        opp = teams.get(g["opponent_team"], {})
        games.append({
            "round": g["round"],
            "opponent": opp.get("short_name", "???"),
            "opponentName": opp.get("name", ""),
            "home": home,
            "goals": g["goals_scored"],
            "for": for_,
            "against": against,
            "date": (g.get("kickoff_time") or "")[:10],
            "xg": round(float(g.get("expected_goals") or 0), 2),
        })
    games.sort(key=lambda x: -x["round"])
    return games


def season_curve(players, last_gw):
    """Cumulative goals for one person at the end of each gameweek so far.

    Derived from the per-match data rather than a stored history, so it cannot
    drift out of step with the totals and needs no state between runs.
    """
    per_gw = [0] * (last_gw + 1)
    for pl in players:
        for g in pl["games"]:
            if 1 <= g["round"] <= last_gw:
                per_gw[g["round"]] += g["goals"]
    curve, running = [], 0
    for gw in range(1, last_gw + 1):
        running += per_gw[gw]
        curve.append(running)
    return curve


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

    # One extra call per distinct pick, for the per-match breakdown.
    wanted = {pid for person in picks["people"] for pid in person["picks"]}
    games_by_id, failed = {}, []
    for pid in sorted(wanted):
        if pid not in elements or not elements[pid]["goals_scored"]:
            games_by_id[pid] = []
            continue
        try:
            games_by_id[pid] = scoring_games(pid, teams)
        except Exception:
            games_by_id[pid] = prev.get(str(pid), {}).get("games", [])
            failed.append(pid)
        time.sleep(0.3)

    finished = [e for e in data["events"] if e.get("finished")]
    current = next((e for e in data["events"] if e.get("is_current")), None)
    played = len(finished)

    scored_in = [g["round"] for gl in games_by_id.values() for g in gl]
    last_gw = max([played] + scored_in) if (played or scored_in) else 0

    missing = []
    people = []
    for order, person in enumerate(picks["people"]):
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
                    "xg": round(float(el.get("expected_goals") or 0), 2),
                    "status": el.get("status", "a"),
                    "news": el.get("news") or "",
                    "chance": el.get("chance_of_playing_next_round"),
                    "games": games_by_id.get(pid, []),
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
                    "xg": old.get("xg", 0),
                    "status": "u",
                    "news": old.get("news", "No longer in the Premier League"),
                    "chance": 0,
                    "games": old.get("games", []),
                })
        total = sum(p["goals"] for p in players)
        players.sort(key=lambda p: -p["goals"])
        club = picks["clubs"].get(person.get("club"), {})
        curve = season_curve(players, last_gw)
        if curve and curve[-1] != total:
            print("warning: %s curve ends on %d but total is %d"
                  % (person["name"], curve[-1], total), file=sys.stderr)
        # Naive pace, flagged as such in the UI: goals so far over a full 38.
        projected = round(total / played * 38) if played else None
        people.append({
            "name": person["name"],
            # Fixed slot from picks.json so a series keeps its colour when the
            # table is re-sorted. Colour follows the person, never their rank.
            "order": order,
            "curve": curve,
            "projected": projected,
            "projectedRemaining": (picks["target"] - projected) if projected is not None else None,
            "xg": round(sum(p["xg"] for p in players), 2),
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
        "lastGameweek": last_gw,
        "totalGameweeks": len(data["events"]),
        "source": "Premier League Fantasy API",
        "sourceUrl": API,
        "clubs": picks["clubs"],
        "people": people,
    }
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")

    if failed:
        print("warning: match history unavailable for %s, kept previous" % failed, file=sys.stderr)
    if missing:
        print("warning: %d pick(s) not in the API, carried over: %s" % (len(missing), missing), file=sys.stderr)
    print("Wrote %s — GW%d, %d gameweeks played" % (OUT, out["gameweek"], played))
    for p in people:
        print("  %d. %-8s %2d goals (%+d vs %d)   on pace for %s"
              % (p["rank"], p["name"], p["total"], -p["remaining"], picks["target"], p["projected"]))
    hurt = [(pl["name"], pl["status"], pl["news"])
            for per in people for pl in per["players"] if pl["status"] != "a"]
    for n, st, news in hurt:
        print("  ! %-22s %s  %s" % (n, st, news))


if __name__ == "__main__":
    main()

"""Snapshot completed Sleeper seasons to local JSON (same schema as the ESPN snapshot).

Completed seasons never change, so we freeze the minimal data the all-time YoY reports
need (per-week team scores + owner identity + final records) once and read from disk
afterward, instead of repeatedly hitting and parsing the Sleeper API.

Starting from the most recent league_id, this walks the `previous_league_id` chain and
snapshots every season whose status is "complete" (the in-progress season is skipped).
Owner identity is stored raw (Sleeper display_name); reconciling it with other platforms
is the all-time reader's job, not the snapshot's.

Sleeper's API is public and read-only — no credentials required.

Usage:
    python scripts/snapshot_sleeper_history.py --league colleagues --league-id 1254271273962319872

Writes ff_bot/data/<league>/<year>.json for each completed season found.
"""

import argparse
import json
import re
from pathlib import Path
from urllib.request import urlopen

API = "https://api.sleeper.app/v1"


def _get(path):
    """GET a Sleeper API path and return parsed JSON."""
    with urlopen(f"{API}/{path}") as resp:
        return json.load(resp)


def _abbrev(name):
    """Derive a short uppercase abbreviation from a team/display name (Sleeper has no abbrev)."""
    letters = re.sub(r"[^A-Za-z0-9]", "", name or "").upper()
    return letters[:4] or "TEAM"


def snapshot_season(league_id):
    """Pull one Sleeper season into the shared snapshot schema.

    Returns (data, previous_league_id, status). `data` is None when the season isn't
    complete, so the caller can skip freezing an in-progress season but still keep walking.
    """
    league = _get(f"league/{league_id}")
    season = int(league["season"])
    status = league.get("status")
    prev = league.get("previous_league_id")
    if status != "complete":
        return None, prev, status

    reg_weeks = league["settings"]["playoff_week_start"] - 1

    # user_id -> display info, and roster_id -> owning user_id
    users = {u["user_id"]: u for u in _get(f"league/{league_id}/users")}
    rosters = _get(f"league/{league_id}/rosters")

    teams = {}
    for r in rosters:
        rid = str(r["roster_id"])
        s = r.get("settings", {})
        owner_id = r.get("owner_id") or (r.get("co_owners") or [None])[0]
        user = users.get(owner_id, {})
        meta = user.get("metadata") or {}
        team_name = meta.get("team_name") or user.get("display_name") or f"Roster {rid}"
        teams[rid] = {
            "owner": user.get("display_name") or "UNKNOWN",
            "team_name": team_name,
            "team_abbrev": _abbrev(team_name),
            "wins": s.get("wins", 0),
            "losses": s.get("losses", 0),
            "ties": s.get("ties", 0),
            "points_for": round(s.get("fpts", 0) + s.get("fpts_decimal", 0) / 100, 2),
        }

    weekly_scores = {}
    for week in range(1, reg_weeks + 1):
        scores = {}
        for entry in _get(f"league/{league_id}/matchups/{week}"):
            pts = entry.get("points")
            if pts is not None:
                scores[str(entry["roster_id"])] = round(pts, 2)
        weekly_scores[str(week)] = scores

    data = {
        "season": season,
        "provider": "sleeper",
        "league_id": int(league_id),
        "regular_season_weeks": reg_weeks,
        "teams": teams,
        "weekly_scores": weekly_scores,
    }
    return data, prev, status


def main():
    parser = argparse.ArgumentParser(description="Snapshot completed Sleeper seasons to JSON.")
    parser.add_argument("--league", required=True, help="league slug for the output dir, e.g. 'colleagues'")
    parser.add_argument("--league-id", required=True, help="most recent Sleeper league_id (chain is walked back)")
    parser.add_argument("--out", default=None, help="output root (default: ff_bot/data)")
    args = parser.parse_args()

    out_root = Path(args.out) if args.out else Path(__file__).resolve().parent.parent / "ff_bot" / "data"
    out_dir = out_root / args.league
    out_dir.mkdir(parents=True, exist_ok=True)

    league_id = args.league_id
    while league_id and league_id != "0":
        data, prev, status = snapshot_season(league_id)
        if data is None:
            print(f"Skipping league {league_id} (status: {status}, not complete)")
        else:
            out_file = out_dir / f"{data['season']}.json"
            with open(out_file, "w") as f:
                json.dump(data, f, indent=2)
            print(f"  wrote {out_file}  ({len(data['teams'])} teams, {len(data['weekly_scores'])} weeks)")
        league_id = prev


if __name__ == "__main__":
    main()

"""One-time-ish snapshot of frozen ESPN seasons to local JSON.

Completed ESPN seasons never change, so we capture the minimal data the all-time
YoY reports need (per-week team scores + owner identity + final records) once and
read from disk afterward, instead of repeatedly hitting and parsing the ESPN API.

Usage (credentials come from the environment):
    LEAGUE_ID=1019976 SWID='{...}' ESPN_S2='...' \\
        python scripts/snapshot_espn_history.py --league colleagues --start 2019 --end 2023

Writes ff_bot/data/espn/<league>/<year>.json for each year in range.
"""

import argparse
import json
import os
from pathlib import Path

from espn_api.football import League


def _owner_name(team):
    """Return a stable owner display name across espn_api versions."""
    # Newer espn_api exposes team.owners (list of dicts); older used team.owner (str).
    owners = getattr(team, "owners", None)
    if owners:
        first = owners[0]
        if isinstance(first, dict):
            name = f"{first.get('firstName', '')} {first.get('lastName', '')}".strip()
            return name or first.get("displayName", "") or "UNKNOWN"
        return str(first)
    return getattr(team, "owner", None) or "UNKNOWN"


def snapshot_year(league_id, year, swid, espn_s2):
    """Pull one frozen season into the snapshot dict described in the module docstring."""
    league = League(league_id=league_id, year=year, swid=swid, espn_s2=espn_s2)
    reg_weeks = league.settings.reg_season_count

    teams = {}
    for t in league.teams:
        teams[str(t.team_id)] = {
            "owner": _owner_name(t),
            "team_name": t.team_name,
            "team_abbrev": t.team_abbrev,
            "wins": t.wins,
            "losses": t.losses,
            "ties": t.ties,
            "points_for": round(t.points_for, 2),
        }

    weekly_scores = {}
    for week in range(1, reg_weeks + 1):
        scores = {}
        for box in league.box_scores(week):
            # away_team is 0 on a bye; skip those half-matchups.
            if box.home_team and box.home_team != 0:
                scores[str(box.home_team.team_id)] = round(box.home_score, 2)
            if box.away_team and box.away_team != 0:
                scores[str(box.away_team.team_id)] = round(box.away_score, 2)
        weekly_scores[str(week)] = scores

    return {
        "season": year,
        "provider": "espn",
        "league_id": league_id,
        "regular_season_weeks": reg_weeks,
        "teams": teams,
        "weekly_scores": weekly_scores,
    }


def main():
    parser = argparse.ArgumentParser(description="Snapshot frozen ESPN seasons to JSON.")
    parser.add_argument("--league", required=True, help="league slug for the output dir, e.g. 'colleagues'")
    parser.add_argument("--start", type=int, required=True, help="first season to snapshot (inclusive)")
    parser.add_argument("--end", type=int, required=True, help="last season to snapshot (inclusive)")
    parser.add_argument("--out", default=None, help="output root (default: ff_bot/data/espn)")
    args = parser.parse_args()

    league_id = int(os.environ["LEAGUE_ID"])
    swid = os.environ["SWID"]
    espn_s2 = os.environ["ESPN_S2"]

    out_root = Path(args.out) if args.out else Path(__file__).resolve().parent.parent / "ff_bot" / "data" / "espn"
    out_dir = out_root / args.league
    out_dir.mkdir(parents=True, exist_ok=True)

    for year in range(args.start, args.end + 1):
        print(f"Snapshotting {args.league} {year} ...")
        data = snapshot_year(league_id, year, swid, espn_s2)
        out_file = out_dir / f"{year}.json"
        with open(out_file, "w") as f:
            json.dump(data, f, indent=2)
        n_weeks = len(data["weekly_scores"])
        n_teams = len(data["teams"])
        print(f"  wrote {out_file}  ({n_teams} teams, {n_weeks} weeks)")


if __name__ == "__main__":
    main()

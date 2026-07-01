"""Thin client over Sleeper's public read-only HTTP API (no auth required).

Wraps the endpoints the live weekly reports need and caches the few responses that
are stable within a run. The one heavy call — the ~5MB global players map — is cached
to disk per day (Sleeper asks callers to fetch it at most once daily), keyed by date.
"""

import datetime
import json
import os
import re
import tempfile
from urllib.request import urlopen

API = "https://api.sleeper.app/v1"

# Process-lifetime cache for the global players map (keyed by date string).
_PLAYERS_CACHE = {}


def _get(path):
    """GET a Sleeper API path and return parsed JSON."""
    with urlopen(f"{API}/{path}") as resp:
        return json.load(resp)


def abbrev(name):
    """Derive a short uppercase tag from a team name (Sleeper has no team_abbrev)."""
    letters = re.sub(r"[^A-Za-z0-9]", "", name or "").upper()
    return letters[:4] or "TEAM"


class SleeperClient:
    """Accessor for one Sleeper league, with light per-run caching."""

    def __init__(self, league_id):
        self.league_id = str(league_id)
        self._league = None
        self._users = None
        self._rosters = None

    def league(self):
        if self._league is None:
            self._league = _get(f"league/{self.league_id}")
        return self._league

    def users(self):
        if self._users is None:
            self._users = _get(f"league/{self.league_id}/users")
        return self._users

    def rosters(self):
        if self._rosters is None:
            self._rosters = _get(f"league/{self.league_id}/rosters")
        return self._rosters

    def matchups(self, week):
        """Raw matchup entries for a week (each: roster_id, points, starters, players_points, ...)."""
        return _get(f"league/{self.league_id}/matchups/{week}")

    def transactions(self, week):
        """All transactions (adds/drops/trades) reported for the given week/round."""
        return _get(f"league/{self.league_id}/transactions/{week}")

    @staticmethod
    def state():
        """Global NFL state (current season, week, season_type)."""
        return _get("state/nfl")

    def players(self):
        """Global player map (id -> {full_name, position, team, injury_status, ...}), cached per day."""
        today = datetime.date.today().isoformat()
        if _PLAYERS_CACHE.get("date") == today:
            return _PLAYERS_CACHE["data"]

        cache_file = os.path.join(tempfile.gettempdir(), f"ff_bot_sleeper_players_{today}.json")
        if os.path.exists(cache_file):
            with open(cache_file) as f:
                data = json.load(f)
        else:
            data = _get("players/nfl")
            with open(cache_file, "w") as f:
                json.dump(data, f)

        _PLAYERS_CACHE.clear()
        _PLAYERS_CACHE.update(date=today, data=data)
        return data

    # -- derived helpers ---------------------------------------------------

    def regular_season_weeks(self):
        return self.league()["settings"]["playoff_week_start"] - 1

    def current_week(self):
        """Current NFL week from global state (0 in the offseason/preseason)."""
        return self.state().get("week", 0)

    def is_faab(self):
        """True if the league uses FAAB bidding for waivers."""
        settings = self.league()["settings"]
        return settings.get("waiver_type") == 2 or settings.get("waiver_budget", 0) > 0

    def teams(self):
        """roster_id (str) -> {owner, team_name, abbrev, wins, losses, ties, points_for}."""
        users = {u["user_id"]: u for u in self.users()}
        out = {}
        for r in self.rosters():
            rid = str(r["roster_id"])
            s = r.get("settings", {})
            owner_id = r.get("owner_id") or (r.get("co_owners") or [None])[0]
            user = users.get(owner_id, {})
            meta = user.get("metadata") or {}
            team_name = meta.get("team_name") or user.get("display_name") or f"Roster {rid}"
            out[rid] = {
                "owner": user.get("display_name") or "UNKNOWN",
                "team_name": team_name,
                "abbrev": abbrev(team_name),
                "wins": s.get("wins", 0),
                "losses": s.get("losses", 0),
                "ties": s.get("ties", 0),
                "points_for": round(s.get("fpts", 0) + s.get("fpts_decimal", 0) / 100, 2),
            }
        return out

    def paired_matchups(self, week):
        """Return the week's games as (home_entry, away_entry) tuples, pairing on matchup_id."""
        by_matchup = {}
        for entry in self.matchups(week):
            mid = entry.get("matchup_id")
            if mid is None:
                continue
            by_matchup.setdefault(mid, []).append(entry)
        return [tuple(pair) for pair in by_matchup.values() if len(pair) == 2]

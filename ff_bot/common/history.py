"""All-time (year-over-year) reports built from frozen season snapshots.

Reads the per-season JSON snapshots under ``ff_bot/data/<league>/`` and aggregates
them across seasons into all-time leaderboards. Because the snapshots share one
provider-agnostic shape, these reports span the ESPN and Sleeper eras seamlessly.

Owner identity is reconciled to a single canonical person per league via the optional
``owners.json`` crosswalk (ESPN stores a full name, Sleeper a display_name). For a
league that only ever lived on one platform the crosswalk can be omitted — the
provider's own identity is then used directly as the canonical key.

Snapshots are completed seasons only; folding in a live in-progress season is a future
extension (see ``_collect`` for where extra seasons would slot in).
"""

import json
from collections import defaultdict
from pathlib import Path

from ff_bot.common.power_rankings import compute_power_rankings
from ff_bot.common.expected_wins import expected_win_record, win_pct

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _league_dir(league, data_dir=None):
    root = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    return root / league


def load_snapshots(league, data_dir=None):
    """Load every frozen season for a league, sorted oldest-first."""
    league_dir = _league_dir(league, data_dir)
    seasons = []
    for path in league_dir.glob("[0-9]*.json"):
        with open(path) as f:
            seasons.append(json.load(f))
    seasons.sort(key=lambda s: s["season"])
    return seasons


def load_crosswalk(league, data_dir=None):
    """Return (espn_key -> canonical, sleeper_name -> canonical) maps; empty if no owners.json."""
    path = _league_dir(league, data_dir) / "owners.json"
    if not path.exists():
        return {}, {}
    with open(path) as f:
        owners = json.load(f)["owners"]
    espn_to_canon = {}
    sleeper_to_canon = {}
    for canonical, ids in owners.items():
        if ids.get("espn_key"):
            espn_to_canon[ids["espn_key"]] = canonical
        if ids.get("sleeper"):
            sleeper_to_canon[ids["sleeper"]] = canonical
    return espn_to_canon, sleeper_to_canon


def _identity(team, provider, espn_to_canon, sleeper_to_canon):
    """Return (key, display) for a team's owner.

    The key is what owners are aggregated by across seasons; display is what's shown.
    Resolution order:
      1. An explicit owners.json crosswalk entry (cross-platform leagues like colleagues).
      2. ESPN's stable owner GUID, when present (single-provider ESPN leagues like dale) —
         robust to name changes and first-name collisions that broke the old name-keying.
      3. Fall back to the provider's own identity (ESPN name token / Sleeper display_name).
    """
    owner = team["owner"]
    if provider == "espn":
        token = owner.upper().split(" ", 1)[0]
        if token in espn_to_canon:
            canonical = espn_to_canon[token]
            return canonical, canonical
        owner_id = team.get("owner_id")
        if owner_id:
            return owner_id, owner
        return token, owner
    if owner in sleeper_to_canon:
        canonical = sleeper_to_canon[owner]
        return canonical, canonical
    return owner, owner


def _owner_map(snapshot, espn_to_canon, sleeper_to_canon):
    """Build team_id -> (key, display) for one season's snapshot."""
    provider = snapshot["provider"]
    return {
        tid: _identity(team, provider, espn_to_canon, sleeper_to_canon)
        for tid, team in snapshot["teams"].items()
    }


def _games(snapshot, owner_of):
    """Yield head-to-head games as (key_a, score_a, key_b, score_b) tuples."""
    for week in snapshot["matchups"].values():
        for m in week:
            yield (owner_of[m["home"]][0], m["home_score"],
                   owner_of[m["away"]][0], m["away_score"])


def _weekly_scores(snapshot, owner_of):
    """Yield per-week {owner_key: score} maps."""
    for week in snapshot["matchups"].values():
        scores = {}
        for m in week:
            scores[owner_of[m["home"]][0]] = m["home_score"]
            scores[owner_of[m["away"]][0]] = m["away_score"]
        yield scores


def _collect(league, data_dir=None):
    """Load snapshots + crosswalk and return (seasons, espn_to_canon, sleeper_to_canon)."""
    seasons = load_snapshots(league, data_dir)
    espn_to_canon, sleeper_to_canon = load_crosswalk(league, data_dir)
    return seasons, espn_to_canon, sleeper_to_canon


def _fmt_pct(pct):
    """Format a win pct the way the reports do: 3 decimals, no leading zero (.625)."""
    return f"{pct:.3f}".lstrip("0")


def get_all_time_power_rankings(league, data_dir=None):
    """All-time power rankings: each season's power score summed per owner, plus extremes."""
    seasons, e2c, s2c = _collect(league, data_dir)
    if not seasons:
        return ""

    totals = defaultdict(float)
    display = {}   # owner key -> most recent display name
    best = None    # (score, display_name, season)
    worst = None
    for snap in seasons:  # oldest-first, so later seasons overwrite the display name
        owner_of = _owner_map(snap, e2c, s2c)
        for key, name in owner_of.values():
            display[key] = name
        rankings = compute_power_rankings(_games(snap, owner_of))
        for score, key in rankings:
            totals[key] += score
            if best is None or score > best[0]:
                best = (score, display[key], snap["season"])
            if worst is None or score < worst[0]:
                worst = (score, display[key], snap["season"])

    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    span = (seasons[0]["season"], seasons[-1]["season"])

    text = [f"🏆 All-Time Power Rankings {span[0]}-{span[1]} 🏆"]
    text += [f"{round(total, 1)} - {display[key]}" for key, total in ranked]
    high = [f"\n🥇 High Single Season PR 🥇\n{best[1]} - {best[2]}: {best[0]}"]
    low = [f"🚮 Low Single Season PR 🚮\n{worst[1]} - {worst[2]}: {worst[0]}"]
    return "\n".join(text + high + low)


def get_all_time_expected_wins(league, data_dir=None):
    """All-time expected wins: each season's all-play-all record summed per owner, plus extremes."""
    seasons, e2c, s2c = _collect(league, data_dir)
    if not seasons:
        return ""

    totals = defaultdict(lambda: {"wins": 0, "losses": 0, "ties": 0})
    display = {}   # owner key -> most recent display name
    best = None    # (wins, record_str, display_name, season)
    worst = None
    for snap in seasons:  # oldest-first, so later seasons overwrite the display name
        owner_of = _owner_map(snap, e2c, s2c)
        for key, name in owner_of.values():
            display[key] = name
        records = expected_win_record(_weekly_scores(snap, owner_of))
        for key, rec in records.items():
            totals[key]["wins"] += rec["wins"]
            totals[key]["losses"] += rec["losses"]
            totals[key]["ties"] += rec["ties"]

            rec_str = f"{rec['wins']}-{rec['losses']}-{rec['ties']} ({_fmt_pct(win_pct(rec))})"
            if best is None or rec["wins"] > best[0]:
                best = (rec["wins"], rec_str, display[key], snap["season"])
            if worst is None or rec["wins"] < worst[0]:
                worst = (rec["wins"], rec_str, display[key], snap["season"])

    ranked = sorted(totals.items(), key=lambda kv: kv[1]["wins"], reverse=True)
    span = (seasons[0]["season"], seasons[-1]["season"])

    text = [f"🏆 All-Time Expected Wins {span[0]}-{span[1]} 🏆"]
    for key, rec in ranked:
        text.append(f"{rec['wins']}-{rec['losses']}-{rec['ties']} ({_fmt_pct(win_pct(rec))}) - {display[key]}")
    high = [f"\n🥇 High Single Season Exp Wins 🥇\n{best[2]} - {best[3]}: {best[1]}"]
    low = [f"🚮 Low Single Season Exp Wins 🚮\n{worst[2]} - {worst[3]}: {worst[1]}"]
    return "\n".join(text + high + low)

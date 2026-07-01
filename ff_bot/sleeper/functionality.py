"""Live weekly reports for a Sleeper league.

Mirrors the ESPN report functions (ff_bot/espn/functionality.py) but reads live data
from Sleeper via SleeperClient, producing the same message text so the bot output is
consistent across providers. Shared metrics (power rankings, expected wins) come from
ff_bot.common so both providers compute them identically.

Not portable from Sleeper's public API (intentionally omitted):
  * projected scores  -> get_projected_scoreboard and the achiever trophy have no source.
  * live "yet to play" player state -> get_monitor is an injury watch only, and
    get_close_scores can't restrict to games still in progress.
Power rankings use the common computed metric (no ESPN playoff_pct equivalent).
"""

from collections import defaultdict

import ff_bot.utils as utils
from ff_bot.common.power_rankings import compute_power_rankings
from ff_bot.common.expected_wins import expected_win_record as _expected_win_record, win_pct

# Sleeper starter slot -> eligible player positions, for optimal-lineup fills.
SLOT_ELIGIBILITY = {
    "QB": {"QB"}, "RB": {"RB"}, "WR": {"WR"}, "TE": {"TE"}, "K": {"K"}, "DEF": {"DEF"},
    "FLEX": {"RB", "WR", "TE"}, "REC_FLEX": {"WR", "TE"}, "WRRB_FLEX": {"RB", "WR"},
    "SUPER_FLEX": {"QB", "RB", "WR", "TE"},
    "DL": {"DL", "DE", "DT"}, "LB": {"LB"}, "DB": {"DB", "CB", "S"},
    "IDP_FLEX": {"DL", "DE", "DT", "LB", "DB", "CB", "S"},
}
NON_STARTER_SLOTS = {"BN", "IR", "TAXI"}


def _player_name(pid, players):
    """Human-readable name for a Sleeper player id (team code for defenses)."""
    p = players.get(pid)
    if not p:
        return pid
    if p.get("position") == "DEF":
        return f"{p.get('team', pid)} D/ST"
    return p.get("full_name") or pid


def _position(pid, players):
    return (players.get(pid) or {}).get("position")


def get_scoreboard_short(client, week):
    """Compact scoreboard of actual scores for the week."""
    teams = client.teams()
    lines = ["Score Update"]
    for home, away in client.paired_matchups(week):
        h = teams[str(home["roster_id"])]
        a = teams[str(away["roster_id"])]
        lines.append(f"{h['abbrev']} {home['points']:.2f} - {away['points']:.2f} {a['abbrev']}")
    return "\n".join(lines)


def get_matchups(client, league_name, week):
    """This week's matchups with each team's record, plus a random league phrase."""
    teams = client.teams()
    lines = ["This Week's Matchups"]
    for home, away in client.paired_matchups(week):
        h = teams[str(home["roster_id"])]
        a = teams[str(away["roster_id"])]
        lines.append(f"{h['team_name']} ({h['wins']}-{h['losses']}) vs "
                     f"{a['team_name']} ({a['wins']}-{a['losses']})")
    lines += ["\n"] + utils.random_phrase(league_name)
    return "\n".join(lines)


def get_close_scores(client, week):
    """Matchups within ~16 points. (Sleeper can't tell which games are still in progress.)"""
    teams = client.teams()
    score = []
    for home, away in client.paired_matchups(week):
        if 0 < abs(home["points"] - away["points"]) < 16:
            h = teams[str(home["roster_id"])]
            a = teams[str(away["roster_id"])]
            score.append(f"{h['abbrev']} {home['points']:.2f} - {away['points']:.2f} {a['abbrev']}")
    if not score:
        return ""
    return "\n".join(["Close Scores"] + score)


def _top_half_wins(client, week, totals):
    """Add a win to each team scoring in the top half of the league for the given week."""
    scores = []
    for home, away in client.paired_matchups(week):
        scores.append((home["points"], str(home["roster_id"])))
        scores.append((away["points"], str(away["roster_id"])))
    scores.sort(key=lambda t: t[0], reverse=True)
    for _, rid in scores[:len(scores) // 2]:
        totals[rid] += 1
    return totals


def get_standings(client, top_half_scoring, week=None):
    """Current standings by wins then points-for, optionally folding in top-half bonus wins."""
    teams = client.teams()
    if not top_half_scoring:
        standings = sorted(
            teams.values(), key=lambda t: (t["wins"], t["points_for"]), reverse=True)
        rows = [f"{i + 1}: {t['team_name']} ({t['wins']} - {t['losses']}) (PF: {t['points_for']})"
                for i, t in enumerate(standings)]
        return "\n".join(["Current Standings:"] + rows)

    if week is None:
        week = client.current_week()
    bonus = defaultdict(int)
    for w in range(1, week):
        _top_half_wins(client, w, bonus)

    enriched = []
    for rid, t in teams.items():
        enriched.append((t["wins"] + bonus[rid], t["losses"], t["team_name"], t["points_for"], bonus[rid]))
    enriched.sort(key=lambda x: (x[0], x[3]), reverse=True)
    rows = [f"{i + 1}: {name} ({wins} - {losses}) (PF: {pf}) (+{b})"
            for i, (wins, losses, name, pf, b) in enumerate(enriched)]
    return "\n".join(["Current Standings:"] + rows)


def _season_games(client, through_week):
    """All head-to-head games weeks 1..through_week as (rid_a, score_a, rid_b, score_b)."""
    games = []
    for w in range(1, through_week + 1):
        for home, away in client.paired_matchups(w):
            games.append((str(home["roster_id"]), home["points"],
                          str(away["roster_id"]), away["points"]))
    return games


def _season_weekly_scores(client, through_week):
    """Per-week {roster_id: score} maps for weeks 1..through_week."""
    weeks = []
    for w in range(1, through_week + 1):
        scores = {}
        for home, away in client.paired_matchups(w):
            scores[str(home["roster_id"])] = home["points"]
            scores[str(away["roster_id"])] = away["points"]
        weeks.append(scores)
    return weeks


def expected_win_record(client, through_week):
    """All-play-all expected records through the given week, sorted by wins (roster_id keyed)."""
    records = _expected_win_record(_season_weekly_scores(client, through_week))
    return sorted(records.items(), key=lambda kv: kv[1]["wins"], reverse=True)


def get_expected_win_total(client, through_week):
    """League expected-wins leaderboard through the given week."""
    teams = client.teams()
    records = expected_win_record(client, through_week)
    rows = [f"{r['wins']}-{r['losses']}-{r['ties']} "
            f"({f'{win_pct(r):.3f}'.lstrip('0')}) - {teams[rid]['team_name']}"
            for rid, r in records]
    return "\n".join(["League Expected Wins %"] + rows)


def get_power_rankings(client, through_week):
    """Computed power rankings through the given week (two-step dominance blend)."""
    teams = client.teams()
    rankings = compute_power_rankings(_season_games(client, through_week))
    rows = [f"{score} - {teams[rid]['team_name']}" for score, rid in rankings]
    return "\n".join(["Power Rankings"] + rows)


def _optimal_lineup_score(entry, players, starter_slots):
    """Return (optimal, actual, pct) for one team's week from players_points + slot layout.

    Greedy fill mirroring the ESPN optimizer: fill the most-restrictive slots first,
    each with the highest-scoring eligible player not already used.
    """
    pool = defaultdict(dict)  # position -> {pid: points}
    for pid, pts in entry["players_points"].items():
        pool[_position(pid, players)][pid] = pts

    actual = sum(entry.get("starters_points") or [])
    used = set()
    optimal = 0.0
    for slot in sorted(starter_slots, key=lambda s: len(SLOT_ELIGIBILITY.get(s, {s}))):
        eligible = SLOT_ELIGIBILITY.get(slot, {slot})
        best = None
        for pos in eligible:
            for pid, pts in pool.get(pos, {}).items():
                if pid in used:
                    continue
                if best is None or pts > best[1]:
                    best = (pid, pts)
        if best:
            used.add(best[0])
            optimal += best[1]

    pct = (actual / optimal * 100) if optimal else 0.0
    return optimal, actual, pct


def optimal_team_scores(client, week, full_report=False):
    """Best-possible vs actual lineup for each team; full ranked report or best/worst summary."""
    players = client.players()
    teams = client.teams()
    starter_slots = [s for s in client.league()["roster_positions"] if s not in NON_STARTER_SLOTS]

    scored = {}  # roster_id -> (optimal, actual, pct)
    for home, away in client.paired_matchups(week):
        for entry in (home, away):
            scored[str(entry["roster_id"])] = _optimal_lineup_score(entry, players, starter_slots)

    ranked = sorted(scored.items(), key=lambda kv: kv[1][2], reverse=True)

    if full_report:
        rows = [f"{i + 1:2d}: {teams[rid]['abbrev']} - {opt:.2f} ({act:.2f} - {pct:.2f}%)"
                for i, (rid, (opt, act, pct)) in enumerate(ranked)]
        return "\n".join(["Optimal Scores - (Actual - % of optimal)"] + rows)

    best_rid, (b_opt, b_act, b_pct) = ranked[0]
    worst_rid, (w_opt, w_act, w_pct) = ranked[-1]
    best = ["🤖 Best Manager 🤖",
            f"{teams[best_rid]['team_name']} scored {b_pct:.2f}% of their optimal score!"]
    worst = ["🤡 Worst Manager 🤡",
             f"{teams[worst_rid]['team_name']} left {w_opt - w_act:.2f} points on their bench. "
             f"Only scoring {w_pct:.2f}% of their optimal score."]
    return best + worst


def get_lucky_trophy(client, week):
    """Lucky (won with a weak score vs the league) and unlucky (lost with a strong one)."""
    teams = client.teams()
    weekly = {}  # roster_id -> (points, 'W'/'L')
    for home, away in client.paired_matchups(week):
        hr, ar = str(home["roster_id"]), str(away["roster_id"])
        if home["points"] > away["points"]:
            weekly[hr] = (home["points"], "W")
            weekly[ar] = (away["points"], "L")
        else:
            weekly[hr] = (home["points"], "L")
            weekly[ar] = (away["points"], "W")

    by_score = sorted(weekly.items(), key=lambda kv: kv[1][0], reverse=True)
    num = len(by_score) - 1

    unlucky_rid = unlucky_rec = None
    for losses, (rid, (_, res)) in enumerate(by_score):
        if res == "L":
            unlucky_rid, unlucky_rec = rid, f"{num - losses}-{losses}"
            break
    lucky_rid = lucky_rec = None
    for wins, (rid, (_, res)) in enumerate(reversed(by_score)):
        if res == "W":
            lucky_rid, lucky_rec = rid, f"{wins}-{num - wins}"
            break

    lucky = ["🍀 Lucky 🍀",
             f"{teams[lucky_rid]['team_name']} was {lucky_rec} against the league, but still got the W"]
    unlucky = ["😡 Unlucky 😡",
               f"{teams[unlucky_rid]['team_name']} was {unlucky_rec} against the league, but still took an L"]
    return lucky + unlucky


def get_trophies(client, week):
    """Weekly trophies: high/low score, blowout, closest win, lucky/unlucky, and optimal-lineup awards.

    (No achiever trophy — that needs projections, which Sleeper's public API doesn't provide.)
    """
    teams = client.teams()
    low_score, low_rid = 9999, None
    high_score, high_rid = -1, None
    closest, close_win, close_lose = 9999, None, None
    blowout, blow_win, blow_lose = -1, None, None

    for home, away in client.paired_matchups(week):
        hr, ar = str(home["roster_id"]), str(away["roster_id"])
        hs, as_ = home["points"], away["points"]
        for score, rid in ((hs, hr), (as_, ar)):
            if score > high_score:
                high_score, high_rid = score, rid
            if score < low_score:
                low_score, low_rid = score, rid
        margin = abs(hs - as_)
        winner, loser = (hr, ar) if hs >= as_ else (ar, hr)
        if margin != 0 and margin < closest:
            closest, close_win, close_lose = margin, winner, loser
        if margin > blowout:
            blowout, blow_win, blow_lose = margin, winner, loser

    def name(rid):
        return teams[rid]["team_name"]

    trophies = [
        "Trophies of the week:",
        "👑 High score 👑", f"{name(high_rid)} with {high_score:.2f} points",
        "💩 Low score 💩", f"{name(low_rid)} with {low_score:.2f} points",
        "😱 Blow out 😱", f"{name(blow_win)} blew out {name(blow_lose)} by {blowout:.2f} points",
        "😅 Close win 😅", f"{name(close_win)} barely beat {name(close_lose)} by {closest:.2f} points",
    ]
    return "\n".join(trophies + get_lucky_trophy(client, week) + optimal_team_scores(client, week))


def get_monitor(client, week):
    """Injury watch: starters carrying an injury designation this week.

    (Sleeper's public API doesn't expose whether a player has already played, so unlike
    the ESPN monitor this is a pure injury flag, not an unplayed-and-injured filter.)
    """
    players = client.players()
    teams = client.teams()
    monitor = []
    for home, away in client.paired_matchups(week):
        for entry in (home, away):
            flagged = []
            for pid in entry.get("starters", []):
                status = (players.get(pid) or {}).get("injury_status")
                if status:
                    pos = _position(pid, players) or "?"
                    flagged.append(f"{pos} {_player_name(pid, players)} - {status}")
            if flagged:
                team_name = teams[str(entry["roster_id"])]["team_name"]
                monitor.append(f"{team_name}:\n" + "\n".join(flagged))

    if not monitor:
        return "No Players to Monitor this week. Good Luck!"
    return "\n".join(["Starting Players to Monitor: "] + monitor)


def get_waiver_report(client, week):
    """Completed waiver/free-agent adds (with FAAB bids when the league uses FAAB) for the week."""
    players = client.players()
    teams = client.teams()
    faab = client.is_faab()
    report = []

    for tx in client.transactions(week):
        if tx.get("status") != "complete" or tx.get("type") not in ("waiver", "free_agent"):
            continue
        adds = tx.get("adds") or {}
        drops = tx.get("drops") or {}
        bid = (tx.get("settings") or {}).get("waiver_bid")
        for pid, rid in adds.items():
            team_name = teams[str(rid)]["team_name"]
            added = f"{_position(pid, players)} {_player_name(pid, players)}"
            line = f"{team_name}\nADDED {added}"
            if faab and bid is not None:
                line += f" (${bid})"
            dropped = [dp for dp, dr in drops.items() if dr == rid]
            if dropped:
                dp = dropped[0]
                line += f"\nDROPPED {_position(dp, players)} {_player_name(dp, players)}"
            report.append(line)

    if not report:
        return "No waiver transactions"
    return "\n".join([f"Waiver Report (Week {week}): "] + report)


def get_final(client, week):
    """End-of-week wrap: final scoreboard followed by the weekly trophies."""
    return f"Final {get_scoreboard_short(client, week)}\n\n{get_trophies(client, week)}"

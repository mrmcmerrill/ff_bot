"""Provider-agnostic power rankings computed from head-to-head game results.

Every data source the bot uses — live ESPN, live Sleeper, and the frozen season
snapshots — can express a season as a list of head-to-head games (two teams, two
scores). This module turns that single common shape into a power ranking, so the
same metric is used everywhere instead of ESPN's proprietary one.

The metric mirrors the spirit of ESPN's old ranking: a blend of two-step dominance,
total points scored, and average margin, weighted 80/15/5. Two-step dominance is the
classic head-to-head measure — a team is rewarded for beating opponents, and rewarded
again for beating opponents who themselves beat others.

A "game" is a 4-tuple ``(team_a, score_a, team_b, score_b)``; team keys may be any
hashable (team objects, ids, or canonical owner names). The public entry point is
``compute_power_rankings``.
"""

from collections import defaultdict

# Blend weights: two-step dominance, total points, average margin.
DEFAULT_WEIGHTS = (0.80, 0.15, 0.05)


def _win_matrix(games):
    """Build the head-to-head win matrix from games.

    Returns ``wins`` where ``wins[a][b]`` is how many times a beat b (a tie counts
    as half a win to each side), plus the full set of team keys seen.
    """
    wins = defaultdict(lambda: defaultdict(float))
    teams = set()
    for a, sa, b, sb in games:
        teams.add(a)
        teams.add(b)
        if sa > sb:
            wins[a][b] += 1
        elif sb > sa:
            wins[b][a] += 1
        else:  # tie — split the credit
            wins[a][b] += 0.5
            wins[b][a] += 0.5
    return wins, teams


def two_step_dominance(games):
    """Return each team's two-step dominance score from head-to-head games.

    Direct dominance is the team's total wins. Two-step dominance adds credit for
    beating teams that were themselves dominant: it is the row sum of ``W + W²``,
    where ``W`` is the win matrix. Exposed separately so it can be tested in isolation.
    """
    wins, teams = _win_matrix(games)

    # Direct dominance: total wins for each team.
    direct = {t: sum(wins[t].values()) for t in teams}

    # Indirect (two-step): beating team c is worth c's own direct dominance.
    dominance = {}
    for t in teams:
        indirect = sum(beat_count * direct[c] for c, beat_count in wins[t].items())
        dominance[t] = direct[t] + indirect
    return dominance


def _points_and_margin(games):
    """Return per-team total points scored and average margin (points for minus against)."""
    points = defaultdict(float)
    margin_total = defaultdict(float)
    game_count = defaultdict(int)
    for a, sa, b, sb in games:
        points[a] += sa
        points[b] += sb
        margin_total[a] += sa - sb
        margin_total[b] += sb - sa
        game_count[a] += 1
        game_count[b] += 1
    avg_margin = {t: margin_total[t] / game_count[t] for t in game_count}
    return dict(points), avg_margin


def _normalize(values):
    """Min-max scale a {key: value} map into [0, 1]; all-equal inputs map to 1.0."""
    if not values:
        return {}
    lo = min(values.values())
    hi = max(values.values())
    if hi == lo:
        return {k: 1.0 for k in values}
    return {k: (v - lo) / (hi - lo) for k, v in values.items()}


def compute_power_rankings(games, weights=DEFAULT_WEIGHTS):
    """Compute power rankings from head-to-head games.

    Parameters
    ----------
    games : iterable of (team_a, score_a, team_b, score_b)
        Every head-to-head game in the period being ranked (e.g. one regular season).
    weights : tuple of (dominance, points, margin)
        Blend weights; defaults to 80/15/5.

    Returns
    -------
    list of (power_score, team_key)
        Sorted highest-first. ``power_score`` is on a 0-100 scale for readability.
    """
    games = list(games)
    dominance = two_step_dominance(games)
    points, avg_margin = _points_and_margin(games)

    norm_dom = _normalize(dominance)
    norm_pts = _normalize(points)
    norm_margin = _normalize(avg_margin)

    w_dom, w_pts, w_margin = weights
    rankings = []
    for team in dominance:
        score = 100 * (
            w_dom * norm_dom[team]
            + w_pts * norm_pts[team]
            + w_margin * norm_margin[team]
        )
        rankings.append((round(score, 1), team))

    rankings.sort(key=lambda x: x[0], reverse=True)
    return rankings

"""Provider-agnostic expected win record ("all-play-all") from weekly scores.

Each week, a team is credited with a win for every other team it outscored, a loss
for every team that outscored it, and a tie on an exact match. Summed over the weeks,
this measures how a team would have fared against the entire league rather than just
its scheduled opponent. Operates on the one shape every data source shares — per-week
score maps — so it works for live providers and frozen snapshots alike.
"""

from collections import defaultdict


def expected_win_record(weekly_scores):
    """Compute each team's all-play-all record across the given weeks.

    Parameters
    ----------
    weekly_scores : iterable of dict
        One ``{team_key: score}`` map per week. Team keys may be any hashable.

    Returns
    -------
    dict
        ``{team_key: {'wins': int, 'losses': int, 'ties': int}}``.
    """
    totals = defaultdict(lambda: {'wins': 0, 'losses': 0, 'ties': 0})

    for week in weekly_scores:
        items = list(week.items())
        for team, score in items:
            for opp, opp_score in items:
                if opp == team:
                    continue
                if score > opp_score:
                    totals[team]['wins'] += 1
                elif score < opp_score:
                    totals[team]['losses'] += 1
                else:
                    totals[team]['ties'] += 1

    return dict(totals)


def win_pct(record):
    """Return win percentage from a {'wins','losses','ties'} record (ties count as half)."""
    opps = record['wins'] + record['losses'] + record['ties']
    if not opps:
        return 0.0
    return round((record['wins'] + 0.5 * record['ties']) / opps, 3)

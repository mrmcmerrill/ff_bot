from datetime import date
from operator import itemgetter
from espn_api.football import League
import ff_bot.utils as utils


def get_scoreboard_short(league, week=None):
    """Return a compact scoreboard of actual scores for the given week (current week if None)."""
    box_scores = league.box_scores(week=week)
    score = [f"{i.home_team.team_abbrev} {i.home_score:.2f} - {i.away_score:.2f} {i.away_team.team_abbrev}"
             for i in box_scores if i.away_team]
    text = ['Score Update'] + score
    return '\n'.join(text)


def get_projected_scoreboard(league, week=None):
    """Return a scoreboard using projected (rather than actual) totals for the given week."""
    box_scores = league.box_scores(week=week)
    score = [f"{i.home_team.team_abbrev} {get_projected_total(i.home_lineup):.2f} - "
             f"{get_projected_total(i.away_lineup):.2f} {i.away_team.team_abbrev}"
             for i in box_scores if i.away_team]
    text = ['Approximate Projected Scores'] + score
    return '\n'.join(text)


def get_expected_win_total(league, week=None):
    """Return each team's expected win/loss record, sorted, based on how they'd fare against the whole league each week."""
    exp_win_rec = expected_win_record(league, week=week)
    records = [f"{i[1]['wins']}-{i[1]['losses']}-{i[1]['ties']} ({i[1]['pct']}) - {i[0].team_name}"
               for i in exp_win_rec]
    text = ['League Expected Wins %'] + records
    return '\n'.join(text)


def get_yoy_expected_win_record(league_id, swid, espn_s2, league_year_start, year):
    """Aggregate expected wins across every season from league_year_start to year.

    Returns an all-time expected-wins leaderboard plus the best and worst single-season
    expected records. Owners are keyed by the first token of their (uppercased) name so
    they stay consistent across seasons even if team names change.
    """
    league = League(league_id=league_id, year=year, swid=swid, espn_s2=espn_s2)
    league_years = list(range(league_year_start, year + 1))

    # owner -> {season -> record}; primed with zeros so every owner/season cell exists
    year_expected_dict = {
        i.owner.upper().split(" ", 1)[0]: {
            x: {'wins': 0, 'losses': 0, 'ties': 0, 'pct': 0.0}
            for x in league_years
        }
        for i in league.teams
    }

    for yoy_year in league_years:
        league = League(league_id=league_id, year=yoy_year, swid=swid, espn_s2=espn_s2)

        # Past seasons use the full regular season (15 weeks since 2022, 14 before);
        # the current season only counts weeks that have already finished.
        if yoy_year != year:
            current_week = 15 if yoy_year >= 2022 else 14
        else:
            current_week = league.current_week - 1

        temp_expected = expected_win_record(league, current_week)

        for team in temp_expected:
            owner_key = team[0].owner.upper().split(" ", 1)[0]
            year_expected_dict[owner_key][yoy_year]['wins'] = team[1]['wins']
            year_expected_dict[owner_key][yoy_year]['losses'] = team[1]['losses']
            year_expected_dict[owner_key][yoy_year]['ties'] = team[1]['ties']
            year_expected_dict[owner_key][yoy_year]['pct'] = team[1]['pct']

    total_team_expected = {
        i.owner.upper().split(" ", 1)[0]: {'wins': 0, 'losses': 0, 'ties': 0, 'pct': 0.0}
        for i in league.teams
    }

    low_score = 9999
    low_score_owner = ''
    low_score_year = ''
    low_score_out = ''
    high_score = -1
    high_score_owner = ''
    high_score_year = ''
    high_score_out = ''

    for owner in year_expected_dict:
        for yr in year_expected_dict[owner]:
            temp_wins = int(year_expected_dict[owner][yr]['wins'])
            temp_losses = int(year_expected_dict[owner][yr]['losses'])
            temp_ties = int(year_expected_dict[owner][yr]['ties'])
            temp_opps = temp_wins + temp_losses + temp_ties
            temp_pct = round(temp_wins / temp_opps, 3)

            if temp_wins > high_score:
                high_score = temp_wins
                high_score_out = f"{temp_wins}-{temp_losses}-{temp_ties} ({temp_pct:.3f}".lstrip('0') + ")"
                high_score_owner = str(owner)
                high_score_year = str(yr)
            elif temp_wins < low_score:
                low_score = temp_wins
                low_score_out = f"{temp_wins}-{temp_losses}-{temp_ties} ({temp_pct:.3f}".lstrip('0') + ")"
                low_score_owner = str(owner)
                low_score_year = str(yr)

            total_team_expected[owner]['wins'] += temp_wins
            total_team_expected[owner]['losses'] += temp_losses
            total_team_expected[owner]['ties'] += temp_ties

            temp_total_opps = (total_team_expected[owner]['wins'] +
                               total_team_expected[owner]['losses'] +
                               total_team_expected[owner]['ties'])
            temp_total_pct = round(total_team_expected[owner]['wins'] / temp_total_opps, 3)
            total_team_expected[owner]['pct'] = f"{temp_total_pct:.3f}".lstrip('0')

    total_team_expected_sorted = sorted(total_team_expected.items(), key=lambda x: x[1]['wins'], reverse=True)

    total_team_expected_wins = [
        f"{i[1]['wins']}-{i[1]['losses']}-{i[1]['ties']} ({i[1]['pct']}) - {i[0]}"
        for i in total_team_expected_sorted if i
    ]

    text = [f"🏆 All-Time Expected Wins {league_year_start}-{year} 🏆"] + total_team_expected_wins
    low_score_text = [f"🚮 Low Single Season Exp Wins 🚮\n{low_score_owner} - {low_score_year}: {low_score_out}"]
    high_score_text = [f"\n🥇 High Single Season Exp Wins 🥇\n{high_score_owner} - {high_score_year}: {high_score_out}"]
    return '\n'.join(text + high_score_text + low_score_text)


def expected_win_record(league, week):
    """Compute each team's expected record up to the given week.

    For every week, each team is scored against every other team's score that week;
    the resulting win/loss/tie tallies are summed across weeks. This measures how a
    team would do against the whole league rather than just its actual opponent.
    Returns a list of (team, record) tuples sorted by expected wins, descending.
    """
    lastWeek = league.current_week
    if week:
        lastWeek = week

    # Per-week projected records and raw scores, plus the season-total accumulator.
    projRecDicts = {i: {x: {'wins': 0, 'losses': 0, 'ties': 0} for x in league.teams} for i in range(lastWeek)}
    teamScoreDicts = {i: {x: None for x in league.teams} for i in range(lastWeek)}
    powerRankingDict = {x: {'wins': 0, 'losses': 0, 'ties': 0, 'pct': 0.0} for x in league.teams}

    for i in range(lastWeek):
        weekNumber = i + 1
        boxes = league.box_scores(weekNumber)
        for box in boxes:
            teamScoreDicts[i][box.home_team] = box.home_score
            teamScoreDicts[i][box.away_team] = box.away_score

        # Tally this team's record as if it had played every other team this week.
        for team in teamScoreDicts[i]:
            wins = 0
            losses = 0
            ties = 0
            oppCount = len(teamScoreDicts[i]) - 1
            for opp in teamScoreDicts[i]:
                if team == opp:
                    continue
                if teamScoreDicts[i][team] > teamScoreDicts[i][opp]:
                    wins += 1
                if teamScoreDicts[i][team] < teamScoreDicts[i][opp]:
                    losses += 1

            if wins + losses != oppCount:  # leftover comparisons were ties
                ties = oppCount - wins - losses

            projRecDicts[i][team]['wins'] = wins
            projRecDicts[i][team]['losses'] = losses
            projRecDicts[i][team]['ties'] = ties

    for team in powerRankingDict:
        totalWins = sum(projRecDicts[i][team]['wins'] for i in range(lastWeek))
        totalLosses = sum(projRecDicts[i][team]['losses'] for i in range(lastWeek))
        totalTies = sum(projRecDicts[i][team]['ties'] for i in range(lastWeek))
        totalOppCount = totalWins + totalLosses + totalTies

        powerRankingDict[team]['wins'] = totalWins
        powerRankingDict[team]['losses'] = totalLosses
        powerRankingDict[team]['ties'] = totalTies
        pctTemp = (float(totalWins) + (0.5 * float(totalTies))) / float(totalOppCount)
        powerRankingDict[team]['pct'] = f"{pctTemp:.3f}".lstrip('0')

    powerRankingDictSorted = sorted(powerRankingDict.items(), key=lambda x: x[1]['wins'], reverse=True)
    return powerRankingDictSorted


def get_standings(league, top_half_scoring, week=None):
    """Return the current standings, sorted by wins then points-for.

    When top_half_scoring is enabled, each team also earns a win for any week it
    scored in the top half of the league, and those bonus wins are folded into the rank.
    """
    standings_txt = ''
    teams = league.teams
    standings = []
    if not top_half_scoring:
        for t in teams:
            standings.append((t.wins, t.losses, t.team_name, t.points_for))

        standings = sorted(standings, key=itemgetter(0, 3), reverse=True)
        standings_txt = [f"{pos + 1}: {team_name} ({wins} - {losses}) (PF: {round(points_for, 2)})"
                         for pos, (wins, losses, team_name, points_for) in enumerate(standings)]
    else:
        top_half_totals = {t.team_name: 0 for t in teams}
        if not week:
            week = league.current_week
        for w in range(1, week):
            top_half_totals = top_half_wins(league, top_half_totals, w)

        for t in teams:
            wins = top_half_totals[t.team_name] + t.wins
            standings.append((wins, t.losses, t.team_name, t.points_for))

        standings = sorted(standings, key=itemgetter(0, 3), reverse=True)
        standings_txt = [
            f"{pos + 1}: {team_name} ({wins} - {losses}) (PF: {round(points_for, 2)}) (+{top_half_totals[team_name]})"
            for pos, (wins, losses, team_name, points_for) in enumerate(standings)
        ]

    text = ["Current Standings:"] + standings_txt
    return "\n".join(text)


def top_half_wins(league, top_half_totals, week):
    """Add a win to each team that scored in the top half of the league for the given week."""
    box_scores = league.box_scores(week=week)

    scores = ([(i.home_score, i.home_team.team_name) for i in box_scores] +
              [(i.away_score, i.away_team.team_name) for i in box_scores if i.away_team])

    scores = sorted(scores, key=lambda tup: tup[0], reverse=True)

    for i in range(0, len(scores) // 2):
        points, team_name = scores[i]
        top_half_totals[team_name] += 1

    return top_half_totals


def get_projected_total(lineup):
    """Sum a lineup's starters, using actual points once a player's game is underway, else projected."""
    total_projected = 0
    for i in lineup:
        if i.slot_position not in ('BE', 'IR'):
            if i.points != 0 or i.game_played > 0:
                total_projected += i.points
            else:
                total_projected += i.projected_points
    return total_projected


def all_played(lineup):
    """Return True if every starter in the lineup has finished their game."""
    for i in lineup:
        if i.slot_position not in ('BE', 'IR') and i.game_played < 100:
            return False
    return True


def get_monitor(league):
    """Return a report of starters who are inactive/injured and yet to play this week."""
    box_scores = league.box_scores()
    monitor = []
    for i in box_scores:
        monitor += scan_roster(i.home_lineup, i.home_team)
        monitor += scan_roster(i.away_lineup, i.away_team)

    if monitor:
        text = ['Starting Players to Monitor: '] + monitor
    else:
        text = ['No Players to Monitor this week. Good Luck!']
    return '\n'.join(text)


def scan_roster(lineup, team):
    """List starters on a team who aren't active/normal and haven't played yet (worth monitoring)."""
    players = []
    for i in lineup:
        if (i.slot_position not in ('BE', 'IR')
                and i.injuryStatus not in ('ACTIVE', 'NORMAL')
                and i.game_played == 0):
            players.append(f"{i.position} {i.name} - {i.injuryStatus.title().replace('_', ' ')}")

    if players:
        player_list = "\n".join(players)
        return [f"{team.team_name}: \n{player_list} \n"]
    return []


def scan_inactives(lineup, team):
    """List starters likely to score nothing (out, doubtful, or non-positive projection) and yet to play."""
    players = []
    for i in lineup:
        if (i.slot_position not in ('BE', 'IR')
                and (i.injuryStatus in ('OUT', 'DOUBTFUL') or i.projected_points <= 0)
                and i.game_played == 0):
            players.append(f"{i.position} {i.name} - {i.injuryStatus.title().replace('_', ' ')}, {i.projected_points} pts")

    if players:
        player_list = "\n".join(players)
        return [f"{team.team_name} likely inactive starting player(s): \n{player_list} \n"]
    return []


def get_matchups(league, league_name, week=None):
    """Return the week's matchups with each team's record, capped with a random league phrase."""
    matchups = league.box_scores(week=week)
    score = [f"{i.home_team.team_name} ({i.home_team.wins}-{i.home_team.losses}) vs "
             f"{i.away_team.team_name} ({i.away_team.wins}-{i.away_team.losses})"
             for i in matchups if i.away_team]
    text = ["This Week's Matchups"] + score + ['\n'] + utils.random_phrase(league_name)
    return '\n'.join(text)


def get_close_scores(league, week=None):
    """Return matchups within ~16 points where the trailing team still has starters left to play."""
    matchups = league.box_scores(week=week)
    score = []

    for i in matchups:
        if i.away_team:
            diffScore = i.away_score - i.home_score
            # Only flag a game if it's close AND the team that's behind can still gain ground.
            if (-16 < diffScore <= 0 and not all_played(i.away_lineup)) or \
               (0 <= diffScore < 16 and not all_played(i.home_lineup)):
                score.append(f"{i.home_team.team_abbrev} {i.home_score:.2f} - {i.away_score:.2f} {i.away_team.team_abbrev}")
    if not score:
        return ''
    text = ['Close Scores'] + score
    return '\n'.join(text)


def get_waiver_report(league, faab):
    """Summarize today's waiver-wire adds/drops, including FAAB bids when faab is enabled."""
    activities = league.recent_activity(50)
    report = []
    today = date.today().strftime('%Y-%m-%d')

    for activity in activities:
        actions = activity.actions
        # activity.date is a millisecond epoch timestamp; only keep today's activity.
        d2 = date.fromtimestamp(activity.date / 1000).strftime('%Y-%m-%d')
        if d2 != today:
            continue

        if len(actions) == 1 and actions[0][1] == 'WAIVER ADDED':
            if faab:
                s = f"{actions[0][0].team_name} \nADDED {actions[0][2].position} {actions[0][2].name} (${actions[0][3]})\n"
            else:
                s = f"{actions[0][0].team_name} \nADDED {actions[0][2].position} {actions[0][2].name}\n"
            report.append(s.lstrip())
        elif len(actions) > 1:
            if actions[0][1] == 'WAIVER ADDED' or actions[1][1] == 'WAIVER ADDED':
                if actions[0][1] == 'WAIVER ADDED':
                    added_idx, dropped_idx = 0, 1
                else:
                    added_idx, dropped_idx = 1, 0

                team_name = actions[0][0].team_name
                added = actions[added_idx][2]
                dropped = actions[dropped_idx][2]
                if faab:
                    s = f"{team_name} \nADDED {added.position} {added.name} (${actions[added_idx][3]})\nDROPPED {dropped.position} {dropped.name}\n"
                else:
                    s = f"{team_name} \nADDED {added.position} {added.name}\nDROPPED {dropped.position} {dropped.name}\n"
                report.append(s.lstrip())

    report.reverse()

    if not report:
        report.append('No waiver transactions')
    else:
        text = [f"Waiver Report {today}: "] + report

    return '\n'.join(text)


def get_starter_counts(league):
    """Infer how many starters each slot position requires by inspecting last week's lineups.

    Returns a dict mapping slot position -> number of starters. Reads from whichever team
    fielded more starters, to guard against the rare matchup with an empty roster slot.
    """
    week = league.current_week - 1
    box_scores = league.box_scores(week=week)

    for i in box_scores:
        h_starters = {}
        h_starter_count = 0
        a_starters = {}
        a_starter_count = 0

        for player in i.home_lineup:
            if player.slot_position not in ('BE', 'IR'):
                h_starter_count += 1
                h_starters[player.slot_position] = h_starters.get(player.slot_position, 0) + 1

        for player in i.away_lineup:
            if player.slot_position not in ('BE', 'IR'):
                a_starter_count += 1
                a_starters[player.slot_position] = a_starters.get(player.slot_position, 0) + 1

        if a_starter_count > h_starter_count:
            return a_starters
        else:
            return h_starters


def best_flex(flexes, player_pool, num):
    """Pick the top `num` scorers eligible for a flex slot across the given positions.

    Returns (best, player_pool): the chosen players and the player_pool with those
    players removed so they can't also be selected for another slot.
    """
    pool = {}
    for flex_position in flexes:
        pool = pool | player_pool.get(flex_position, {})

    pool = dict(sorted(pool.items(), key=lambda item: item[1], reverse=True))
    best = dict(list(pool.items())[:num])

    # Remove the chosen flex players from the pool so they aren't double-counted.
    for pos in player_pool:
        for p in best:
            if p in player_pool[pos]:
                player_pool[pos].pop(p)
    return best, player_pool


def optimal_lineup_score(lineup, starter_counts):
    """Compute the best possible score a lineup could have produced.

    Returns a tuple of (optimal score, actual score, points left on bench,
    actual as a percentage of optimal). Fills required positions with the
    highest scorers first, then resolves flex/OP/DP slots from what remains.
    """
    best_lineup = {}
    position_players = {}

    # Group every player by position, recording the actual lineup's starter score as we go.
    score = 0
    for player in lineup:
        if player.position not in position_players:
            position_players[player.position] = {}
        position_players[player.position][player.name] = player.points
        if player.slot_position not in ('BE', 'IR'):
            score += player.points

    # Fill each fixed position with its highest scorers, leaving the rest for flex slots.
    for position in starter_counts:
        if position in position_players:
            position_players[position] = dict(sorted(
                position_players[position].items(), key=lambda item: item[1], reverse=True))
            best_lineup[position] = dict(list(position_players[position].items())[:starter_counts[position]])
            position_players[position] = dict(list(position_players[position].items())[starter_counts[position]:])
        else:
            best_lineup[position] = {}

    # Resolve standard flex slots (e.g. "RB/WR/TE"), skipping defensive D/ST slots.
    for position in starter_counts:
        if 'D/ST' not in position and '/' in position:
            flex = position.split('/')
            result = best_flex(flex, position_players, starter_counts[position])
            best_lineup[position] = result[0]
            position_players = result[1]

    # Offensive Player slot: best remaining of any offensive position.
    if 'OP' in starter_counts:
        flex = ['RB', 'WR', 'TE', 'QB']
        result = best_flex(flex, position_players, starter_counts['OP'])
        best_lineup['OP'] = result[0]
        position_players = result[1]

    # Defensive Player slot: best remaining of any individual defensive position.
    if 'DP' in starter_counts:
        flex = ['DT', 'DE', 'LB', 'CB', 'S']
        result = best_flex(flex, position_players, starter_counts['DP'])
        best_lineup['DP'] = result[0]
        position_players = result[1]

    best_score = sum(sum(v.values()) for v in best_lineup.values())
    score_pct = (score / best_score) * 100
    return (best_score, score, best_score - score, score_pct)


def optimal_team_scores(league, week=None, full_report=False):
    """Compare each team's actual score against its optimal lineup for the week.

    With full_report=True, returns a ranked text table of every team's optimal vs actual.
    Otherwise returns a short best-manager / worst-manager summary (the trophy format).
    """
    if not week:
        week = league.current_week - 1
    box_scores = league.box_scores(week=week)
    results = []
    best_scores = {}
    starter_counts = get_starter_counts(league)

    for i in box_scores:
        if i.home_team != 0:
            best_scores[i.home_team] = optimal_lineup_score(i.home_lineup, starter_counts)
        if i.away_team != 0:
            best_scores[i.away_team] = optimal_lineup_score(i.away_lineup, starter_counts)

    best_scores = dict(sorted(best_scores.items(), key=lambda item: item[1][3], reverse=True))

    if full_report:
        for i, score in enumerate(best_scores, 1):
            s = f"{i:2d}: {score.team_abbrev} - {best_scores[score][0]:.2f} ({best_scores[score][1]:.2f} - {best_scores[score][3]:.2f}%)"
            results.append(s)

        text = ['Optimal Scores - (Actual - % of optimal)'] + results
        return '\n'.join(text)
    else:
        num_teams = 0
        team_names = ''
        for score in best_scores:
            if best_scores[score][3] > 99.8:
                num_teams += 1
                team_names += score.team_name + ', '
            else:
                break

        if num_teams <= 1:
            best = next(iter(best_scores.items()))
            best_mgr_str = ['🤖 Best Manager 🤖',
                            f"{best[0].team_name} scored {best[1][3]:.2f}% of their optimal score!"]
        else:
            team_names = team_names[:-2]
            best_mgr_str = ['🤖 Best Managers 🤖',
                            f"{team_names} scored their optimal score!"]

        worst = best_scores.popitem()
        worst_mgr_str = ['🤡 Worst Manager 🤡',
                         f"{worst[0].team_name} left {worst[1][0] - worst[1][1]:.2f} points on their bench. "
                         f"Only scoring {worst[1][3]:.2f}% of their optimal score."]
        return best_mgr_str + worst_mgr_str


def get_power_rankings(league, week=None):
    """Return the week's power rankings (two-step dominance weighted with scoring and margin) plus playoff odds."""
    if not week:
        week = league.current_week
    power_rankings = league.power_rankings(week=week)

    score = [f"{i[0]} ({i[1].playoff_pct:.1f}) - {i[1].team_name}"
             for i in power_rankings if i]
    text = ['Power Rankings (Playoff %)'] + score
    return '\n'.join(text)


def get_yoy_power_rankings(league_id, swid, espn_s2, league_year_start, year):
    """Sum each owner's final power-ranking score across every season into an all-time leaderboard.

    Also reports the single best and worst season power-ranking scores. Like the YoY expected-wins
    report, owners are keyed by the first token of their name to stay stable across seasons.
    """
    league_years = list(range(league_year_start, year + 1))
    league = League(league_id=league_id, year=year)

    team_rankings = {
        i.owner.upper().split(" ", 1)[0]: {x: 0.0 for x in league_years}
        for i in league.teams
    }

    for yoy_year in league_years:
        league = League(league_id=league_id, year=yoy_year, swid=swid, espn_s2=espn_s2)

        # Past seasons use the full regular season; current season counts finished weeks only.
        if yoy_year != year:
            current_week = 15 if yoy_year >= 2022 else 14
        else:
            current_week = league.current_week - 1

        power_rankings = league.power_rankings(week=current_week)

        for i in power_rankings:
            team_rankings[i[1].owner.upper().split(" ", 1)[0]][yoy_year] = i[0]

    alltime_total = {i.owner.upper().split(" ", 1)[0]: 0.0 for i in league.teams}

    low_score = 9999.9
    low_score_owner = ''
    low_score_year = 0
    high_score = -1.1
    high_score_owner = ''
    high_score_year = 0

    for owner in team_rankings:
        for yr in team_rankings[owner]:
            score_val = float(team_rankings[owner][yr])
            if score_val > high_score:
                high_score = score_val
                high_score_owner = owner
                high_score_year = yr
            elif score_val < low_score:
                low_score = score_val
                low_score_owner = owner
                low_score_year = yr

            alltime_total[owner] = round(alltime_total[owner] + score_val, 2)

    alltime_total_sorted = sorted(alltime_total.items(), key=lambda x: x[1], reverse=True)
    alltime_score = [f"{score[1]} - {score[0]}" for score in alltime_total_sorted if score]

    text = [f"🏆 All-Time Power Rankings {league_year_start}-{year} 🏆"] + alltime_score
    low_score_text = [f"🚮 Low Single Season PR 🚮\n{low_score_owner} - {low_score_year}: {low_score}"]
    high_score_text = [f"\n🥇 High Single Season PR 🥇\n{high_score_owner} - {high_score_year}: {high_score}"]
    return '\n'.join(text + high_score_text + low_score_text)


def get_lucky_trophy(league, week=None):
    """Award the 'lucky' team (won despite a poor score vs the league) and the 'unlucky' team (lost despite a strong one)."""
    box_scores = league.box_scores(week=week)
    weekly_scores = {}
    for i in box_scores:
        if i.home_score > i.away_score:
            weekly_scores[i.home_team] = [i.home_score, 'W']
            weekly_scores[i.away_team] = [i.away_score, 'L']
        else:
            weekly_scores[i.home_team] = [i.home_score, 'L']
            weekly_scores[i.away_team] = [i.away_score, 'W']
    weekly_scores = dict(sorted(weekly_scores.items(), key=lambda item: item[1], reverse=True))

    num_teams = len(weekly_scores) - 1

    losses = 0
    unlucky_team_name = ''
    unlucky_record = ''
    for t in weekly_scores:
        if weekly_scores[t][1] == 'L':
            unlucky_team_name = t.team_name
            unlucky_record = f"{num_teams - losses}-{losses}"
            break
        losses += 1

    wins = 0
    lucky_team_name = ''
    lucky_record = ''
    weekly_scores = dict(sorted(weekly_scores.items(), key=lambda item: item[1]))
    for t in weekly_scores:
        if weekly_scores[t][1] == 'W':
            lucky_team_name = t.team_name
            lucky_record = f"{wins}-{num_teams - wins}"
            break
        wins += 1

    lucky_str = ['🍀 Lucky 🍀',
                 f"{lucky_team_name} was {lucky_record} against the league, but still got the W"]
    unlucky_str = ['😡 Unlucky 😡',
                   f"{unlucky_team_name} was {unlucky_record} against the league, but still took an L"]
    return lucky_str + unlucky_str


def get_achiever_trophy(league, week=None):
    """Award the teams that most beat (overachiever) and most missed (underachiever) their projected score."""
    box_scores = league.box_scores(week=week)
    over_achiever = ''
    under_achiever = ''
    high_achiever_str = ['📈 Overachiever 📈']
    low_achiever_str = ['📉 Underachiever 📉']
    best_performance = -9999
    worst_performance = 9999
    for i in box_scores:
        home_performance = i.home_score - i.home_projected
        away_performance = i.away_score - i.away_projected

        if home_performance > best_performance:
            best_performance = home_performance
            over_achiever = i.home_team.team_name
        if home_performance < worst_performance:
            worst_performance = home_performance
            under_achiever = i.home_team.team_name
        if away_performance > best_performance:
            best_performance = away_performance
            over_achiever = i.away_team.team_name
        if away_performance < worst_performance:
            worst_performance = away_performance
            under_achiever = i.away_team.team_name

    if best_performance > 0:
        high_achiever_str.append(f"{over_achiever} was {best_performance:.2f} points over their projection")
    else:
        high_achiever_str.append('No team out performed their projection')

    if worst_performance < 0:
        low_achiever_str.append(f"{under_achiever} was {abs(worst_performance):.2f} points under their projection")
    else:
        low_achiever_str.append('No team was worse than their projection')

    return high_achiever_str + low_achiever_str


def get_trophies(league, week=None):
    """Build the full weekly trophy roundup: high/low score, blowout, closest win, plus the lucky, achiever, and optimal-lineup awards."""
    matchups = league.box_scores(week=week)
    low_score = 9999
    low_team_name = ''
    high_score = -1
    high_team_name = ''
    closest_score = 9999
    close_winner = ''
    close_loser = ''
    biggest_blowout = -1
    blown_out_team_name = ''
    ownerer_team_name = ''

    for i in matchups:
        if i.home_score > high_score:
            high_score = i.home_score
            high_team_name = i.home_team.team_name
        if i.home_score < low_score:
            low_score = i.home_score
            low_team_name = i.home_team.team_name
        if i.away_score > high_score:
            high_score = i.away_score
            high_team_name = i.away_team.team_name
        if i.away_score < low_score:
            low_score = i.away_score
            low_team_name = i.away_team.team_name
        if i.away_score - i.home_score != 0 and abs(i.away_score - i.home_score) < closest_score:
            closest_score = abs(i.away_score - i.home_score)
            if i.away_score - i.home_score < 0:
                close_winner = i.home_team.team_name
                close_loser = i.away_team.team_name
            else:
                close_winner = i.away_team.team_name
                close_loser = i.home_team.team_name
        if abs(i.away_score - i.home_score) > biggest_blowout:
            biggest_blowout = abs(i.away_score - i.home_score)
            if i.away_score - i.home_score < 0:
                ownerer_team_name = i.home_team.team_name
                blown_out_team_name = i.away_team.team_name
            else:
                ownerer_team_name = i.away_team.team_name
                blown_out_team_name = i.home_team.team_name

    high_score_str = ['👑 High score 👑', f"{high_team_name} with {high_score:.2f} points"]
    low_score_str = ['💩 Low score 💩', f"{low_team_name} with {low_score:.2f} points"]
    close_score_str = ['😅 Close win 😅', f"{close_winner} barely beat {close_loser} by {closest_score:.2f} points"]
    blowout_str = ['😱 Blow out 😱', f"{ownerer_team_name} blew out {blown_out_team_name} by {biggest_blowout:.2f} points"]

    text = (['Trophies of the week:'] + high_score_str + low_score_str + blowout_str + close_score_str +
            get_lucky_trophy(league, week) + get_achiever_trophy(league, week) + optimal_team_scores(league, week))
    return '\n'.join(text)

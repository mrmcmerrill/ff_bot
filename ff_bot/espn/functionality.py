from datetime import date
import ff_bot.utils as utils
import datetime
from datetime import date
from operator import itemgetter, attrgetter
from espn_api.football import League

def get_scoreboard_short(league, week=None):
    # Gets current week's scoreboard
    box_scores = league.box_scores(week=week)
    score = ['%4s %.2f - %.2f %4s' % (i.home_team.team_abbrev, i.home_score,
                                    i.away_score, i.away_team.team_abbrev) for i in box_scores
             if i.away_team]
    text = ['Score Update'] + score
    return '\n'.join(text)

def get_projected_scoreboard(league, week=None):
    # Gets current week's scoreboard projections
    box_scores = league.box_scores(week=week)
    score = ['%4s %.2f - %.2f %4s' % (i.home_team.team_abbrev, get_projected_total(i.home_lineup),
                                    get_projected_total(i.away_lineup), i.away_team.team_abbrev) for i in box_scores
             if i.away_team]
    text = ['Approximate Projected Scores'] + score
    return '\n'.join(text)

def get_expected_win_total(league, week=None):
    exp_win_rec = expected_win_record(league, week=week)
    records = []

    for i in exp_win_rec:
        records += ['%s-%s-%s (%s) - %s' % (i[1]['wins'], i[1]['losses'], i[1]['ties'], i[1]['pct'], i[0].team_name,)]

    text = ['League Expected Wins %'] + records

    return '\n'.join(text)

def get_yoy_expected_win_record(league_id, swid, espn_s2, league_year_start, year):
    league = League(league_id=league_id, year=year, swid=swid, espn_s2=espn_s2)
    
    total_league_years = year - league_year_start
    league_years = []
    
    for i in range(total_league_years + 1):
        year_iterator = league_year_start + i
        league_years.append(year_iterator)
  
    # initialize the dictionary for the per year splits
    # year_expected_dict = {i: {x.owner.upper().split(" ", 1)[0]: {'wins': int, 'losses': int, 'ties': int, 'pct': float} for x in league.teams} for i in league_years}
    year_expected_dict = {i.owner.upper().split(" ", 1)[0]: {x: {'wins': int, 'losses': int, 'ties': int, 'pct': float} for x in league_years} for i in league.teams} 
    
    for yoy_year in league_years:
        league = League(league_id=league_id, year=yoy_year, swid=swid, espn_s2=espn_s2) 
        current_week = None
        
        if yoy_year != year:
            if yoy_year >= 2022:
                current_week = 15
            else:
                current_week = 14
        else:    
            if not current_week:
                current_week = league.current_week - 1
                
        temp_expected = expected_win_record(league, current_week)
        
        for team in temp_expected:
            year_expected_dict[team[0].owner.upper().split(" ", 1)[0]][yoy_year]['wins'] = team[1]['wins']
            year_expected_dict[team[0].owner.upper().split(" ", 1)[0]][yoy_year]['losses'] = team[1]['losses']
            year_expected_dict[team[0].owner.upper().split(" ", 1)[0]][yoy_year]['ties'] = team[1]['ties']
            year_expected_dict[team[0].owner.upper().split(" ", 1)[0]][yoy_year]['pct'] = team[1]['pct']
    
    # print(year_expected_dict)
    
    # initialize the dictionary for the final by team expected wins
    total_team_expected = {i.owner.upper().split(" ", 1)[0]: {'wins': 0, 'losses': 0, 'ties': 0, 'pct': 0.0} for i in league.teams} 
    
    temp_wins = int
    temp_losses = int
    temp_ties = int
    temp_total_opps = int
    temp_pct = float
    
    low_score = int(9999)
    low_score_owner = ''
    low_score_year = ''
    high_score = int(-1)
    high_score_owner = ''
    high_score_year = ''
    
    for owner in year_expected_dict:
        for year in year_expected_dict[owner]:
            temp_wins = int(year_expected_dict[owner][year]['wins'])
            temp_losses = int(year_expected_dict[owner][year]['losses'])
            temp_ties = int(year_expected_dict[owner][year]['ties'])
            temp_opps = temp_wins + temp_losses + temp_ties
            temp_pct = round(temp_wins / temp_opps, 3)
            
            if temp_wins > high_score:
                high_score = temp_wins
                high_score_out = '%s-%s-%s (%s)' % (temp_wins, temp_losses, temp_ties, '{:.3f}'.format(temp_pct).lstrip('0'))
                high_score_owner = str(owner)
                high_score_year = str(year)
            elif temp_wins < low_score:
                low_score = temp_wins
                low_score_out = '%s-%s-%s (%s)' % (temp_wins, temp_losses, temp_ties, '{:.3f}'.format(temp_pct).lstrip('0'))
                low_score_owner = str(owner)
                low_score_year = str(year)
                       
            total_team_expected[owner]['wins'] = total_team_expected[owner]['wins'] + temp_wins
            total_team_expected[owner]['losses'] = total_team_expected[owner]['losses'] + temp_losses
            total_team_expected[owner]['ties'] = total_team_expected[owner]['ties'] + temp_ties
            
            temp_total_opps = total_team_expected[owner]['wins'] + total_team_expected[owner]['losses'] + total_team_expected[owner]['ties']
            temp_total_pct = round(total_team_expected[owner]['wins'] / temp_total_opps, 3)
            total_team_expected[owner]['pct'] = '{:.3f}'.format(temp_total_pct).lstrip('0')
    
    # print(total_team_expected)
    
    total_team_expected_sorted = sorted(total_team_expected.items(), key=lambda x: x[1]['wins'], reverse=True)
    # print(total_team_expected_sorted)
    
    total_team_expected_wins = ['%s-%s-%s (%s) - %s' % (i[1]['wins'], i[1]['losses'], i[1]['ties'], i[1]['pct'], i[0]) for i in total_team_expected_sorted if i]
    
    text = ['🏆 All-Time Expected Wins %s-%s 🏆' % (league_year_start, year)] + total_team_expected_wins
    low_score_text = ['🚮 Low Single Season Exp Wins 🚮' + '\n' '%s - %s: %s' % (low_score_owner, low_score_year, low_score_out)]
    high_score_text = ['\n🥇 High Single Season Exp Wins 🥇' + '\n' + '%s - %s: %s' % (high_score_owner, high_score_year, high_score_out)]
    return '\n'.join(text + high_score_text + low_score_text)

def expected_win_record(league, week):
    # This script gets expected win record, given an already-connected league and a week to look at. Requires espn_api

    # Get what week most recently passed
    lastWeek = league.current_week

    if week:
        lastWeek = week

    # initialize dictionaries to stash the projected record/expected wins for each week, and to stash each team's score for each week
    projRecDicts = {i: {x: {'wins': int, 'losses': int, 'ties': int} for x in league.teams} for i in range(lastWeek)}
    teamScoreDicts = {i: {x: None for x in league.teams} for i in range(lastWeek)}

    # initialize the dictionary for the final power ranking
    powerRankingDict = {x: {'wins': int, 'losses': int, 'ties': int, 'pct': float} for x in league.teams}

    for i in range(lastWeek):  # for each week that has been played
        weekNumber = i+1  # set the week
        boxes = league.box_scores(weekNumber)  # pull box scores from that week
        for box in boxes:  # for each boxscore
            teamScoreDicts[i][box.home_team] = box.home_score  # plug the home team's score into the dict
            teamScoreDicts[i][box.away_team] = box.away_score  # and the away team's

        for team in teamScoreDicts[i].keys():  # for each team
            wins = 0
            losses = 0
            ties = 0
            oppCount = len(list(teamScoreDicts[i].keys()))-1
            for opp in teamScoreDicts[i].keys():  # for each potential opponent
                if team == opp:  # skip yourself
                    continue
                if teamScoreDicts[i][team] > teamScoreDicts[i][opp]:  # win case
                    wins += 1
                if teamScoreDicts[i][team] < teamScoreDicts[i][opp]:  # loss case
                    losses += 1

            if wins + losses != oppCount:  # in case of an unlikely tie
                ties = oppCount - wins - losses

            # store the team's projected record for that week
            
            projRecDicts[i][team]['wins'] = wins
            projRecDicts[i][team]['losses'] = losses
            projRecDicts[i][team]['ties'] = ties
            #print(projRecDicts[i][team])

    for team in powerRankingDict.keys():  # for each team
        # total up the expected wins from each week, divide by the number of weeks
        totalWins = sum([projRecDicts[i][team]['wins'] for i in range(lastWeek)])
        totalLosses = sum([projRecDicts[i][team]['losses'] for i in range(lastWeek)])
        totalTies = sum([projRecDicts[i][team]['ties'] for i in range(lastWeek)])
        totalOppCount = totalWins + totalLosses + totalTies
        
        powerRankingDict[team]['wins'] = totalWins
        powerRankingDict[team]['losses'] = totalLosses
        powerRankingDict[team]['ties'] = totalTies
        pctTemp = (float(totalWins) + (0.5*float(totalTies))) / float(totalOppCount)
        powerRankingDict[team]['pct'] = '{:.3f}'.format(pctTemp).lstrip('0')

    powerRankingDictSorted = sorted(powerRankingDict.items(), key=lambda x: x[1]['wins'], reverse=True)
    
    # powerRankingDictSortedTemp = {k: v for k, v in sorted(powerRankingDict.items(
    # ), key=lambda item: item[1], reverse=True)}  # sort for presentation purposes
    # powerRankingDictSorted = {x: ('{:.2f}'.format(
    #    powerRankingDictSortedTemp[x]*100)) for x in powerRankingDictSorted.keys()}  # put into a prettier format
    # return in the format that the bot expects
    # recordTextOutput = powerRankingDictSorted[x]
    # return [(powerRankingDictSorted[x], x) for x in powerRankingDictSorted.keys()]
    return (powerRankingDictSorted)  

def get_standings(league, top_half_scoring, week=None):
    standings_txt = ''
    teams = league.teams
    standings = []
    if not top_half_scoring:
        for t in teams:
            standings.append((t.wins, t.losses, t.team_name, t.points_for))

        standings = sorted(standings, key=itemgetter(0,3), reverse=True)
        standings_txt = [f"{pos + 1}: {team_name} ({wins} - {losses}) (PF: {round(points_for, 2)})" for \
            pos, (wins, losses, team_name, points_for) in enumerate(standings)]

    else:
        top_half_totals = {t.team_name: 0 for t in teams}
        if not week:
            week = league.current_week
        for w in range(1, week):
            top_half_totals = top_half_wins(league, top_half_totals, w)

        for t in teams:
            wins = top_half_totals[t.team_name] + t.wins
            standings.append((wins, t.losses, t.team_name, t.points_for))

        standings = sorted(standings, key=itemgetter(0,3), reverse=True)
        standings_txt = [f"{pos + 1}: {team_name} ({wins} - {losses}) (PF: {round(points_for, 2)}) (+{top_half_totals[team_name]})" for \
            pos, (wins, losses, team_name, points_for) in enumerate(standings)]

    text = ["Current Standings:"] + standings_txt

    return "\n".join(text)

def top_half_wins(league, top_half_totals, week):
    box_scores = league.box_scores(week=week)

    scores = [(i.home_score, i.home_team.team_name) for i in box_scores] + \
        [(i.away_score, i.away_team.team_name) for i in box_scores if i.away_team]

    scores = sorted(scores, key=lambda tup: tup[0], reverse=True)

    for i in range(0, len(scores)//2):
        points, team_name = scores[i]
        top_half_totals[team_name] += 1

    return top_half_totals

def get_projected_total(lineup):
    total_projected = 0
    for i in lineup:
        if i.slot_position != 'BE' and i.slot_position != 'IR':
            if i.points != 0 or i.game_played > 0:
                total_projected += i.points
            else:
                total_projected += i.projected_points
    return total_projected

def all_played(lineup):
    for i in lineup:
        if i.slot_position != 'BE' and i.slot_position != 'IR' and i.game_played < 100:
            return False
    return True

def get_monitor(league):
    box_scores = league.box_scores()
    monitor = []
    text = ''
    for i in box_scores:
        monitor += scan_roster(i.home_lineup, i.home_team)
        monitor += scan_roster(i.away_lineup, i.away_team)

    if monitor:
        text = ['Starting Players to Monitor: '] + monitor
    else:
        text = ['No Players to Monitor this week. Good Luck!']
    return '\n'.join(text)

def scan_roster(lineup, team):
    count = 0
    players = []
    for i in lineup:
        if i.slot_position != 'BE' and i.slot_position != 'IR' and \
            i.injuryStatus != 'ACTIVE' and i.injuryStatus != 'NORMAL' \
                and i.game_played == 0:

            count += 1
            player = i.position + ' ' + i.name + ' - ' + i.injuryStatus.title().replace('_', ' ')
            players += [player]

    list = ""
    report = ""

    for p in players:
        list += p + "\n"

    if count > 0:
        s = '%s: \n%s \n' % (team.team_name, list[:-1])
        report = [s.lstrip()]

    return report

def scan_inactives(lineup, team):
    count = 0
    players = []
    for i in lineup:
        if (i.slot_position != 'BE' and i.slot_position != 'IR') \
            and (i.injuryStatus == 'OUT' or i.injuryStatus == 'DOUBTFUL' or i.projected_points <= 0) \
                and i.game_played == 0:
                    count += 1
                    players += ['%s %s - %s, %d pts' %
                                (i.position, i.name, i.injuryStatus.title().replace('_', ' '), i.projected_points)]

    inactive_list = ""
    inactives = ""
    for p in players:
        inactive_list += p + "\n"
    if count > 0:
        s = '%s likely inactive starting player(s): \n%s \n' % (team.team_name, inactive_list[:-1])
        inactives = [s.lstrip()]

    return inactives

def get_matchups(league, league_name, week=None):
    #Gets current week's Matchups
    matchups = league.box_scores(week=week)

    score = ['%s (%s-%s) vs %s (%s-%s)' % (i.home_team.team_name, i.home_team.wins, i.home_team.losses,
                                         i.away_team.team_name, i.away_team.wins, i.away_team.losses) for i in matchups
             if i.away_team]
    text = ['This Week\'s Matchups'] + score + ['\n'] + utils.random_phrase(league_name)
    return '\n'.join(text)

def get_close_scores(league, week=None):
    # Gets current closest scores (15.999 points or closer)
    matchups = league.box_scores(week=week)
    score = []

    for i in matchups:
        if i.away_team:
            diffScore = i.away_score - i.home_score
            if (-16 < diffScore <= 0 and not all_played(i.away_lineup)) or (0 <= diffScore < 16 and not all_played(i.home_lineup)):
                score += ['%s %.2f - %.2f %s' % (i.home_team.team_abbrev, i.home_score,
                                                 i.away_score, i.away_team.team_abbrev)]
    if not score:
        return('')
    text = ['Close Scores'] + score
    return '\n'.join(text)

def get_waiver_report(league, faab):
    activities = league.recent_activity(50)
    report = []
    today = date.today().strftime('%Y-%m-%d')
    # today_test_string = '2022-10-05'
    # date_time_test_obj = datetime.strptime(today_test_string, '%Y-%m-%d')
    # today = date_time_test_obj
    text = ''

    for activity in activities:
        actions = activity.actions
        d2 = date.fromtimestamp(activity.date/1000).strftime('%Y-%m-%d')
        if d2 == today:  # only get waiver activites from today
            if len(actions) == 1 and actions[0][1] == 'WAIVER ADDED':  # player added, but not dropped
                if faab:
                    s = '%s \nADDED %s %s ($%s)\n' % (actions[0][0].team_name,
                                                      actions[0][2].position, actions[0][2].name, actions[0][3])
                else:
                    s = '%s \nADDED %s %s\n' % (actions[0][0].team_name, actions[0][2].position, actions[0][2].name)
                report += [s.lstrip()]
            elif len(actions) > 1:
                if actions[0][1] == 'WAIVER ADDED' or actions[1][1] == 'WAIVER ADDED':
                    if actions[0][1] == 'WAIVER ADDED':
                        if faab:
                            s = '%s \nADDED %s %s ($%s)\nDROPPED %s %s\n' % (
                                actions[0][0].team_name, actions[0][2].position, actions[0][2].name, actions[0][3], actions[1][2].position, actions[1][2].name)
                        else:
                            s = '%s \nADDED %s %s\nDROPPED %s %s\n' % (
                                actions[0][0].team_name, actions[0][2].position, actions[0][2].name, actions[1][2].position, actions[1][2].name)
                    else:
                        if faab:
                            s = '%s \nADDED %s %s ($%s)\nDROPPED %s %s\n' % (
                                actions[0][0].team_name, actions[1][2].position, actions[1][2].name, actions[1][3], actions[0][2].position, actions[0][2].name)
                        else:
                            s = '%s \nADDED %s %s\nDROPPED %s %s\n' % (
                                actions[0][0].team_name, actions[1][2].position, actions[1][2].name, actions[0][2].position, actions[0][2].name)
                    report += [s.lstrip()]

    report.reverse()

    if not report:
        report += ['No waiver transactions']
    else:
        text = ['Waiver Report %s: ' % today] + report

    return '\n'.join(text)

def get_starter_counts(league):
    """
    Get the number of starters for each position

    Parameters
    ----------
    league : object
        The league object for which the starter counts are being generated

    Returns
    -------
    dict
        A dictionary containing the number of players at each position within the starting lineup.
    """

    # Get the current week -1 to get the last week's box scores
    week = league.current_week - 1
    # Get the box scores for the specified week
    box_scores = league.box_scores(week=week)
    # Initialize a dictionary to store the home team's starters and their positions
    h_starters = {}
    # Initialize a variable to keep track of the number of home team starters
    h_starter_count = 0
    # Initialize a dictionary to store the away team's starters and their positions
    a_starters = {}
    # Initialize a variable to keep track of the number of away team starters
    a_starter_count = 0
    # Iterate through each game in the box scores
    for i in box_scores:
        # Iterate through each player in the home team's lineup
        for player in i.home_lineup:
            # Check if the player is a starter (not on the bench or injured)
            if (player.slot_position != 'BE' and player.slot_position != 'IR'):
                # Increment the number of home team starters
                h_starter_count += 1
                try:
                    # Try to increment the count for this position in the h_starters dictionary
                    h_starters[player.slot_position] = h_starters[player.slot_position] + 1
                except KeyError:
                    # If the position is not in the dictionary yet, add it and set the count to 1
                    h_starters[player.slot_position] = 1
        # in the rare case when someone has an empty slot we need to check the other team as well
        for player in i.away_lineup:
            if (player.slot_position != 'BE' and player.slot_position != 'IR'):
                a_starter_count += 1
                try:
                    a_starters[player.slot_position] = a_starters[player.slot_position] + 1
                except KeyError:
                    a_starters[player.slot_position] = 1

        if a_starter_count > h_starter_count:
            return a_starters
        else:
            return h_starters

def best_flex(flexes, player_pool, num):
    """
    Given a list of flex positions, a dictionary of player pool, and a number of players to return,
    this function returns the best flex players from the player pool.

    Parameters
    ----------
    flexes : list
        a list of strings representing the flex positions
    player_pool : dict
        a dictionary with keys as position and values as a dictionary with player name as key and value as score
    num : int
        number of players to return from the player pool

    Returns
    ----------
    best : dict
        a dictionary containing the best flex players from the player pool
    player_pool : dict
        the updated player pool after removing the best flex players
    """

    pool = {}
    # iterate through each flex position
    for flex_position in flexes:
        # add players from flex position to the pool
        try:
            pool = pool | player_pool[flex_position]
        except KeyError:
            pass
    # sort the pool by score in descending order
    pool = {k: v for k, v in sorted(pool.items(), key=lambda item: item[1], reverse=True)}
    # get the top num players from the pool
    best = dict(list(pool.items())[:num])
    # remove the best flex players from the player pool
    for pos in player_pool:
        for p in best:
            if p in player_pool[pos]:
                player_pool[pos].pop(p)
    return best, player_pool

def optimal_lineup_score(lineup, starter_counts):
    """
    This function returns the optimal lineup score based on the provided lineup and starter counts.

    Parameters
    ----------
    lineup : list
        A list of player objects for which the optimal lineup score is being generated
    starter_counts : dict
        A dictionary containing the number of starters for each position

    Returns
    -------
    tuple
        A tuple containing the optimal lineup score, the provided lineup score, the difference between the two scores,
        and the percentage of the provided lineup's score compared to the optimal lineup's score.
    """

    best_lineup = {}
    position_players = {}

    # get all players and points
    score = 0
    for player in lineup:
        try:
            position_players[player.position][player.name] = player.points
        except KeyError:
            position_players[player.position] = {}
            position_players[player.position][player.name] = player.points
        if player.slot_position not in ['BE', 'IR']:
            score += player.points

    # sort players by position for points
    for position in starter_counts:
        try:
            position_players[position] = {k: v for k, v in sorted(
                position_players[position].items(), key=lambda item: item[1], reverse=True)}
            best_lineup[position] = dict(list(position_players[position].items())[:starter_counts[position]])
            position_players[position] = dict(list(position_players[position].items())[starter_counts[position]:])
        except KeyError:
            best_lineup[position] = {}

    # flexes. need to figure out best in other single positions first
    for position in starter_counts:
        # flex
        if 'D/ST' not in position and '/' in position:
            flex = position.split('/')
            result = best_flex(flex, position_players, starter_counts[position])
            best_lineup[position] = result[0]
            position_players = result[1]

    # Offensive Player. need to figure out best in other positions first
    if 'OP' in starter_counts:
        flex = ['RB', 'WR', 'TE', 'QB']
        result = best_flex(flex, position_players, starter_counts['OP'])
        best_lineup['OP'] = result[0]
        position_players = result[1]

    # Defensive Player. need to figure out best in other positions first
    if 'DP' in starter_counts:
        flex = ['DT', 'DE', 'LB', 'CB', 'S']
        result = best_flex(flex, position_players, starter_counts['DP'])
        best_lineup['DP'] = result[0]
        position_players = result[1]

    best_score = 0
    for position in best_lineup:
        best_score += sum(best_lineup[position].values())

    score_pct = (score / best_score) * 100
    return (best_score, score, best_score - score, score_pct)

def optimal_team_scores(league, week=None, full_report=False):
    """
    This function returns the optimal team scores or managers.

    Parameters
    ----------
    league : object
        The league object for which the optimal team scores are being generated
    week : int, optional
        The week for which the optimal team scores are to be returned (default is the previous week)
    full_report : bool, optional
        A boolean indicating if a full report should be returned (default is False)

    Returns
    -------
    str or tuple
        If full_report is True, a string representing the full report of the optimal team scores.
        If full_report is False, a tuple containing the best and worst manager strings.

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

    best_scores = {key: value for key, value in sorted(best_scores.items(), key=lambda item: item[1][3], reverse=True)}

    if full_report:
        i = 1
        for score in best_scores:
            s = ['%2d: %4s: %6.2f (%6.2f - %.2f%%)' %
                 (i, score.team_abbrev, best_scores[score][0],
                  best_scores[score][1], best_scores[score][3])]
            results += s
            i += 1

        text = ['Optimal Scores:  (Actual - % of optimal)'] + results
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
            best_mgr_str = ['🤖 Best Manager 🤖'] + ['%s scored %.2f%% of their optimal score!' % (best[0].team_name, best[1][3])]
        else:
            team_names = team_names[:-2]
            best_mgr_str = ['🤖 Best Managers 🤖'] + [f'{team_names} scored their optimal score!']

        worst = best_scores.popitem()
        worst_mgr_str = ['🤡 Worst Manager 🤡'] + ['%s left %.2f points on their bench. Only scoring %.2f%% of their optimal score.' %
                                                 (worst[0].team_name, worst[1][0] - worst[1][1], worst[1][3])]
        return (best_mgr_str + worst_mgr_str)

def get_power_rankings(league, week=None):
    # power rankings requires an integer value, so this grabs the current week for that
    if not week:
        week = league.current_week
    # Gets current week's power rankings
    # Using 2 step dominance, as well as a combination of points scored and margin of victory.
    # It's weighted 80/15/5 respectively
    power_rankings = league.power_rankings(week=week)

    score = ['%s (%.1f) - %s' % (i[0], i[1].playoff_pct, i[1].team_name) for i in power_rankings
            if i]
    text = ['Power Rankings (Playoff %)'] + score
    return '\n'.join(text)

def get_yoy_power_rankings(league_id, swid, espn_s2, league_year_start, year):
    
    total_league_years = year - league_year_start
    league_years = []
    
    for i in range(total_league_years+1):
        year_iterator = league_year_start + i
        league_years.append(year_iterator)
    
    league = League(league_id=league_id, year=year)

    # initialize the dictionary for the by year and team sorted power rankings
    team_rankings = {i.owner.upper().split(" ", 1)[0]: {x: float for x in league_years} for i in league.teams} 

    # create yoy dict with each year 
    for yoy_year in league_years:        
        league = League(league_id=league_id, year=yoy_year, swid=swid, espn_s2=espn_s2)
        current_week = None
        
        if yoy_year != year:
            if yoy_year >= 2022:
                current_week = 15
            else:
                current_week = 14
        else:    
            if not current_week:
                current_week = league.current_week - 1
            
        power_rankings = league.power_rankings(week=current_week)
        # yearly_score = ['%s - %s' % (i[0], i[1].owner.upper().split(" ", 1)[0]) for i in power_rankings if i]
        # text = ['%s Power Rankings' % (yoy_year)] + yearly_score
        
        for i in power_rankings:
            team_rankings[i[1].owner.upper().split(" ", 1)[0]][yoy_year] = i[0]          
            
    alltime_total = {i.owner.upper().split(" ", 1)[0]: 0.0 for i in league.teams}
    temp_score = float
    
    low_score = 9999.9
    low_score_owner = ''
    low_score_year = 0
    high_score = -1.1
    high_score_owner = ''
    high_score_year = 0
    
    for owner in team_rankings:
        temp_score = 0.0
        for year in team_rankings[owner]:
            if float(team_rankings[owner][year]) > high_score:
                high_score = float(team_rankings[owner][year])
                high_score_owner = owner
                high_score_year = year
            elif float(team_rankings[owner][year]) < low_score:
                low_score = float(team_rankings[owner][year])
                low_score_owner = owner
                low_score_year = year
                
            temp_score = float(team_rankings[owner][year])           
            alltime_total[owner] = round(alltime_total[owner] + temp_score, 2)
    
    alltime_total_sorted = sorted(alltime_total.items(), key=lambda x: x[1], reverse=True)
    alltime_score = ['%s - %s' % (score[1], score[0]) for score in alltime_total_sorted if score]
    
    text = ['🏆 All-Time Power Rankings %s-%s 🏆' % (league_year_start, year)] + alltime_score
    low_score_text = ['🚮 Low Single Season PR 🚮' + '\n' '%s - %s: %s' % (low_score_owner, low_score_year, low_score)]
    high_score_text = ['\n🥇 High Single Season PR 🥇' + '\n' + '%s - %s: %s' % (high_score_owner, high_score_year, high_score)]
    return '\n'.join(text + high_score_text + low_score_text)

def get_lucky_trophy(league, week=None):
    box_scores = league.box_scores(week=week)
    weekly_scores = {}
    for i in box_scores:
        if i.home_score > i.away_score:
            weekly_scores[i.home_team] = [i.home_score,'W']
            weekly_scores[i.away_team] = [i.away_score,'L']
        else:
            weekly_scores[i.home_team] = [i.home_score,'L']
            weekly_scores[i.away_team] = [i.away_score,'W']
    weekly_scores = dict(sorted(weekly_scores.items(), key=lambda item: item[1], reverse=True))

    # losses = 0
    # for t in weekly_scores:
    #     print(t.team_name + ': (' + str(len(weekly_scores)-1-losses) + '-' + str(losses) +')')
    #     losses+=1

    losses = 0
    unlucky_team_name = ''
    unlucky_record = ''
    lucky_team_name = ''
    lucky_record = ''
    num_teams = len(weekly_scores)-1

    for t in weekly_scores:
        if weekly_scores[t][1] == 'L':
            unlucky_team_name = t.team_name
            unlucky_record = str(num_teams-losses) + '-' + str(losses)
            break
        losses += 1

    wins = 0
    weekly_scores = dict(sorted(weekly_scores.items(), key=lambda item: item[1]))
    for t in weekly_scores:
        if weekly_scores[t][1] == 'W':
            lucky_team_name = t.team_name
            lucky_record = str(wins) + '-' + str(num_teams - wins)
            break
        wins += 1

    lucky_str = ['🍀 Lucky 🍀']+['%s was %s against the league, but still got the W' % (lucky_team_name, lucky_record)]
    unlucky_str = ['😡 Unlucky 😡']+['%s was %s against the league, but still took an L' % (unlucky_team_name, unlucky_record)]
    return(lucky_str + unlucky_str)

def get_achiever_trophy(league, week=None):
    """
    Get the teams with biggest difference from projection
    """
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
        high_achiever_str +=['%s was %.2f points over their projection' % (over_achiever, best_performance)]
    else:
        high_achiever_str += ['No team out performed their projection']

    if worst_performance < 0:
        low_achiever_str += ['%s was %.2f points under their projection' % (under_achiever, abs(worst_performance))]
    else:
        low_achiever_str += ['No team was worse than their projection']

    return(high_achiever_str + low_achiever_str)

def get_trophies(league, week=None):
    # Gets trophies for highest score, lowest score, closest score, and biggest win
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
        if i.away_score - i.home_score != 0 and \
                abs(i.away_score - i.home_score) < closest_score:
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

    high_score_str = ['👑 High score 👑']+['%s with %.2f points' % (high_team_name, high_score)]
    low_score_str = ['💩 Low score 💩']+['%s with %.2f points' % (low_team_name, low_score)]
    close_score_str = ['😅 Close win 😅']+['%s barely beat %s by %.2f points' % (close_winner, close_loser, closest_score)]
    blowout_str = ['😱 Blow out 😱']+['%s blew out %s by %.2f points' % (ownerer_team_name, blown_out_team_name, biggest_blowout)]

    text = ['Trophies of the week:'] + high_score_str + low_score_str + blowout_str + close_score_str + get_lucky_trophy(league, week) + get_achiever_trophy(league, week) + optimal_team_scores(league, week)
    return '\n'.join(text)


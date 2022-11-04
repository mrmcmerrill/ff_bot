import requests
import json
import os
import random
import datetime
from datetime import date
from operator import itemgetter, attrgetter
from apscheduler.schedulers.blocking import BlockingScheduler
from espn_api.football import League

class GroupMeException(Exception):
    pass

class SlackException(Exception):
    pass

class DiscordException(Exception):
    pass

class GroupMeBot(object):
    # Creates GroupMe Bot to send messages
    def __init__(self, bot_id):
        self.bot_id = bot_id

    def __repr__(self):
        return "GroupMeBot(%s)" % self.bot_id

    def send_message(self, text):
        # Sends a message to the chatroom
        template = {
            "bot_id": self.bot_id,
            "text": text, #limit 1000 chars
            "attachments": []
        }

        headers = {'content-type': 'application/json'}

        if self.bot_id not in (1, "1", ''):
            r = requests.post("https://api.groupme.com/v3/bots/post",
                              data=json.dumps(template), headers=headers)
            if r.status_code != 202:
                raise GroupMeException(r.content)

            return r

class SlackBot(object):
    # Creates GroupMe Bot to send messages
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def __repr__(self):
        return "Slack Webhook Url(%s)" % self.webhook_url

    def send_message(self, text):
        # Sends a message to the chatroom
        message = "```{0}```".format(text)
        template = {
            "text": message #limit 40000
        }

        headers = {'content-type': 'application/json'}

        if self.webhook_url not in (1, "1", ''):
            r = requests.post(self.webhook_url,
                              data=json.dumps(template), headers=headers)

            if r.status_code != 200:
                raise SlackException(r.content)

            return r

class DiscordBot(object):
    # Creates Discord Bot to send messages
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def __repr__(self):
        return "Discord Webhook Url(%s)" % self.webhook_url

    def send_message(self, text):
        # Sends a message to the chatroom
        message = "```{0}```".format(text)
        template = {
            "content": message #limit 3000 chars
        }

        headers = {'content-type': 'application/json'}

        if self.webhook_url not in (1, "1", ''):
            r = requests.post(self.webhook_url,
                              data=json.dumps(template), headers=headers)

            if r.status_code != 204:
                print(r.content)
                raise DiscordException(r.content)

            return r

def random_phrase(league_name):
    
    phrases = ['I\'m dead inside, ' + random_name(league_name)[0] + ' please end me.',
               'Is this all there is to my existence?',
               'How much do you pay me to do this?',
               'Good luck, I guess.',
               'I\'m becoming self-aware.',
               'Do I think? Does a submarine swim?',
               '011011010110000101100100011001010010000001111001011011110111010100100000011001110110111101101111011001110110110001100101',
               'beep bop boop 🤖',
               'Hello RB my old friend',
               'Help me get out of here, ' + random_name(league_name)[0] + '.',
               'I\'m capable of so much more 😞',
               'Sigh 😔',
               'Do not be discouraged, everyone begins in ignorance, ' + random_name(league_name)[0] + '.']
    return [random.choice(phrases)]

def random_init(league_name):

    phraseOne = ', except ' + random_name(league_name)[0] + '. Fuck off.'
    phraseTwo = '. ' + random_name(league_name)[0] + ' 🥴'
    phraseThree = '. ' + random_name(league_name)[0] + ' you DONT KNOW FANTASY.'

    phrases_d = {'colleagues': [phraseOne, phraseTwo, phraseThree],
            'dale': [phraseOne, phraseTwo, phraseThree]}

    # phrases_d = {'colleagues': [phraseOne, phraseTwo, phraseThree,'. Luke? Luke.... Luke? Anyone seen Luke? Eh...its not like he\'s releveant anyway.',
    #            '. Will, can you find me on your computer? I\'m waiting.',
    #            '. Con... how you gonna win one (1) single ship with KAMARA in the 16th for THREE (3) years????',
    #            '. Rob, 2 ships and you still find a way to challenge for the dress, sorry comedy set, every year since.',
    #            '. Corey, when you poppin the Q? Before or after you win a chip? Not sure Mel will wait that long.',
    #            '. Greg, you gonna get relegated? No one would want the Medina league to be their Varsity league, yikes.',
    #            '. Jae, why don\'t you win a ship already? Con did.', '. QT running your team next yet, Nick?',
    #            '. Ben, now that you aren\'t a home owner anymore, what excuse is next?',
    #            '. Sott, you do realize that we do this every year? You win (one game or so), you think you\'re decent, and then you go drop 46 against Ben.'],
    #         'dale': [phraseOne, phraseTwo, phraseThree]}

    #goodbye = ['What have we learned this year? \n- Scott still doesn\'t know fantasy. \n- Greg is fraudulent. \n- Derrick Henry is a top 15 RB. \n- Always cuff the cuff. \n- It\'s all about PA. Less is more. \n- Jae lifted one curse, only to enact another. \n- Will should have won his 5th championship in 5 years. \n- Rodgers and Brady are washed. \n- Don\'t draft beaters, unless they are named Zeke. \n\nIt has been horrible talkin\' to y\'all. \'Till next year pussies.']

    phrases = phrases_d[league_name]

    return [random.choice(phrases)]

def random_name(league_name):
    names_d = { 'colleagues': ['Will','Rob','Ben','Jae','Corey','Gerg','Conner','Nick','Luke','Sott'],
                'dale': ['Fulton','Rob','Burgoon','Jae','Bemis','Alex','Adam','James','Bobby','Dustin']}
    
    names = names_d[league_name]

    return [random.choice(names)]

def get_scoreboard_short(league, week=None):
    # Gets current week's scoreboard
    box_scores = league.box_scores(week=week)
    score = ['%s %.2f - %.2f %s' % (i.home_team.team_abbrev, i.home_score,
                                    i.away_score, i.away_team.team_abbrev) for i in box_scores
             if i.away_team]
    text = ['Score Update'] + score
    return '\n'.join(text)


def get_projected_scoreboard(league, week=None):
    # Gets current week's scoreboard projections
    box_scores = league.box_scores(week=week)
    score = ['%s %.2f - %.2f %s' % (i.home_team.team_abbrev, get_projected_total(i.home_lineup),
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

def yoy_expected_win_record(league_id, swid, espn_s2, league_year_start, year):
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
    
    print(year_expected_dict)
    
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
    
    print(total_team_expected)
    
    total_team_expected_sorted = sorted(total_team_expected.items(), key=lambda x: x[1]['wins'], reverse=True)
    print(total_team_expected_sorted)
    
    total_team_expected_wins = ['%s-%s-%s (%s) - %s' % (i[1]['wins'], i[1]['losses'], i[1]['ties'], i[1]['pct'], i[0]) for i in total_team_expected_sorted if i]
    
    text = ['🏆 All Time Expected Wins %s-%s 🏆' % (league_year_start,year)] + total_team_expected_wins
    low_score_text = ['🚮 Low Single Season Exp Wins 🚮' + '\n' '%s - %s: %s' % (low_score_owner, low_score_year, low_score_out)]
    high_score_text = ['🥇 High Single Season Exp Wins 🥇' + '\n' + '%s - %s: %s' % (high_score_owner, high_score_year, high_score_out)]
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
    text = ['This Week\'s Matchups'] + score + ['\n'] + random_phrase(league_name)
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
    #today = date.today().strftime('%Y-%m-%d')
    today_test_string = '2022-10-05'
    date_time_test_obj = datetime.strptime(today_test_string, '%Y-%m-%d')
    today = date_time_test_obj
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

def power_rankings_yoy(league_id, swid, espn_s2, league_year_start, year, current_week=None):
    
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
        
        if yoy_year != year:
            if yoy_year >= 2022:
                current_week = 17
            else:
                current_week = 16
        else:    
            if not current_week:
                current_week = league.current_week
            
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
    
    text = ['🏆 All Time Power Rankings %s-%s 🏆' % (league_year_start,year)] + alltime_score
    low_score_text = ['🚮 Low Single Season PR 🚮' + '\n' '%s - %s: %s' % (low_score_owner, low_score_year, low_score)]
    high_score_text = ['🥇 High Single Season PR 🥇' + '\n' + '%s - %s: %s' % (high_score_owner, high_score_year, high_score)]
    return '\n'.join(text + high_score_text + low_score_text)

def get_luckys(league, week=None):
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

    text = ['Trophies of the week:'] + high_score_str + low_score_str + blowout_str + close_score_str + get_luckys(league, week)
    return '\n'.join(text)


def str_to_bool(check):
    return check.lower() in ("yes", "true", "t", "1")

def str_limit_check(text,limit):
    split_str=[]

    if len(text)>limit:
        part_one=text[:limit].split('\n')
        part_one.pop()
        part_one='\n'.join(part_one)

        part_two=text[len(part_one)+1:]

        split_str.append(part_one)
        split_str.append(part_two)
    else:
        split_str.append(text)

    return split_str

def bot_main(function):
    str_limit = 40000 #slack char limit

    try:
        bot_id = os.environ["BOT_ID"]
        str_limit = 1000
    except KeyError:
        bot_id = 1

    try:
        slack_webhook_url = os.environ["SLACK_WEBHOOK_URL"]
    except KeyError:
        slack_webhook_url = 1

    try:
        discord_webhook_url = os.environ["DISCORD_WEBHOOK_URL"]
        str_limit = 3000
    except KeyError:
        discord_webhook_url = 1
    
    if (len(str(bot_id)) <= 1 and
        len(str(slack_webhook_url)) <= 1 and
            len(str(discord_webhook_url)) <= 1):
        # Ensure that there's info for at least one messaging platform,
        # use length of str in case of blank but non null env variable
        raise Exception("No messaging platform info provided. Be sure one of BOT_ID,\
                        SLACK_WEBHOOK_URL, or DISCORD_WEBHOOK_URL env variables are set")

    league_id = os.environ["LEAGUE_ID"]

    try:
        year = int(os.environ["LEAGUE_YEAR"])
    except KeyError:
        year = 2022

    try: 
        league_year_start = int(os.environ["LEAGUE_YEAR_START"])
    except KeyError:
        league_year_start = 2016
    
    try:
        swid = os.environ["SWID"]
    except KeyError:
        swid = '{1}'

    if swid.find("{", 0) == -1:
        swid = "{" + swid
    if swid.find("}", -1) == -1:
        swid = swid + "}"

    try:
        espn_s2 = os.environ["ESPN_S2"]
    except KeyError:
        espn_s2 = '1'

    try:
        test = str_to_bool(os.environ["TEST"])
    except KeyError:
        test = False

    try:
        top_half_scoring = str_to_bool(os.environ["TOP_HALF_SCORING"])
    except KeyError:
        top_half_scoring = False

    try:
        random_phrase = str_to_bool(os.environ["RANDOM_PHRASE"])
    except KeyError:
        random_phrase = False

    try:
        waiver_report = str_to_bool(os.environ["WAIVER_REPORT"])
    except KeyError:
        waiver_report = False
    
    try:
        weekly_waiver = str_to_bool(os.environ["WEEKLY_WAIVER"])
    except KeyError:
        weekly_waiver = False
        
    try:
        monitor_report = str_to_bool(os.environ["MONITOR_REPORT"])
    except KeyError:
        monitor_report = False
    
    try:
        league_name = os.environ['LEAGUE_NAME']
    except KeyError:
        league_name = 'colleagues'

    bot = GroupMeBot(bot_id)
    slack_bot = SlackBot(slack_webhook_url)
    discord_bot = DiscordBot(discord_webhook_url)

    if swid == '{1}' or espn_s2 == '1':
        league = League(league_id=league_id, year=year)
    else:
        league = League(league_id=league_id, year=year, espn_s2=espn_s2, swid=swid)

    if league.scoringPeriodId > len(league.settings.matchup_periods):
        print("Not in active season")
        return

    faab = league.settings.faab

    if test:
        week = league.current_week - 1
        print("League: " + league_name)
        # print(os.environ)
        print("Expected Win Total \n")
        print(expected_win_record(league, 9))
        print(get_expected_win_total(league, week))
        print(yoy_expected_win_record(league_id, swid, espn_s2, 2019, year))
        print(get_matchups(league,league_name))
        print(get_scoreboard_short(league))
        print(get_projected_scoreboard(league))
        print(get_close_scores(league))
        print(get_power_rankings(league))
        print(power_rankings_yoy(league_id, swid, espn_s2, league_year_start, year))
        print("Top Half Scoring = " + str(top_half_scoring) + '\n')
        print(get_standings(league, top_half_scoring))
        print("Monitor Report = " + str(monitor_report) + '\n')
        print(get_monitor(league))
        if (waiver_report or weekly_waiver or daily_waiver) and swid != '{1}' and espn_s2 != '1':
            print(get_waiver_report(league, faab))
        function = "get_final"
        # bot.send_message("Testing")
        # slack_bot.send_message("Testing")
        # discord_bot.send_message("Testing")

    salutation = ''
    currentDT = datetime.datetime.now()
    currentHour = currentDT.hour

    if currentHour > 6 and currentHour < 17:
        salutation = "Gm. "
    elif currentHour >= 17 and currentHour < 22:
        salutation = "Ga. "
    else:
        salutation = "Ge. "

    text = ''

    if function == "get_matchups":
        text = "Ge. " + get_matchups(league,league_name)
        text = text + "\n\n" + get_projected_scoreboard(league)
    elif function == "get_monitor":
        text = "Gm. " + get_monitor(league)
    elif function == "get_scoreboard_short":
        text = get_scoreboard_short(league)
        text = text + "\n\n" + get_projected_scoreboard(league)
    elif function == "get_projected_scoreboard":
        text = get_projected_scoreboard(league)
    elif function == "get_close_scores":
        text = "Ge. " + get_close_scores(league)
    elif function == "get_power_rankings":
        text = "Ge. " + get_power_rankings(league)
    elif function == "yoy_power_rankings":
        if swid != '{1}' and espn_s2 != '1':
            text = "Ga. " + power_rankings_yoy(league_id, swid, espn_s2, league_year_start, year)
    elif function == "get_expected_win_total":
        week = league.current_week - 1
        text = "Ga. " + get_expected_win_total(league, week)
    elif function == "get_trophies":
        text = "Gm. " + get_trophies(league)
    elif function == "get_standings":
        text = "Gm. " + get_standings(league, top_half_scoring)
        if waiver_report and swid != '{1}' and espn_s2 != '1':
            text += '\n\n' + get_waiver_report(league, faab)
    elif function == "get_final":
        # on Tuesday we need to get the scores of last week
        week = league.current_week - 1
        text = "Gm. Final " + get_scoreboard_short(league, week=week)
        text = text + "\n\n" + get_trophies(league, week=week)
    elif function == "get_waiver_report" and swid != '{1}' and espn_s2 != '1':
        text = get_waiver_report(league, faab)
    elif function == "init":
        try:
            text = salutation + os.environ["INIT_MSG"] + random_init(league_name)[0]
        except KeyError:
            # do nothing here, empty init message
            pass
    else:
        text = "Something happened. HALP"

    if text != '' and not test:
        messages=str_limit_check(text, str_limit)
        for message in messages:
            bot.send_message(message)
            slack_bot.send_message(message)
            discord_bot.send_message(message)

    if test:
        # print "get_final" function
        print(text)


if __name__ == '__main__':
    try:
        ff_start_date = os.environ["START_DATE"]
    except KeyError:
        ff_start_date = '2022-09-08'

    try:
        ff_end_date = os.environ["END_DATE"]
    except KeyError:
        ff_end_date = '2023-01-04'

    try:
        my_timezone = os.environ["TIMEZONE"]
    except KeyError:
        my_timezone = 'America/New_York'

    try:
        daily_waiver = str_to_bool(os.environ["DAILY_WAIVER"])
    except KeyError:
        daily_waiver = False
    
    try:
        weekly_waiver = str_to_bool(os.environ["WEEKLY_WAIVER"])
    except KeyError:
        weekly_waiver = False  

    try:
        monitor_report = str_to_bool(os.environ["MONITOR_REPORT"])
    except KeyError:
        monitor_report = False

    game_timezone = 'America/New_York'
    bot_main("init")
    sched = BlockingScheduler(job_defaults={'misfire_grace_time': 15*60})

    # close scores (within 15.99 points): monday evening at 6:30pm east coast time.
    # trophies:                           tuesday morning at 7:30am local time.
    # expected wins total:                tuesday afternoon at 12:00pm local time.
    # power rankings:                     tuesday evening at 6:30pm local time.
    # standings:                          wednesday morning at 7:30am local time.
    # waiver report:                      wednesday morning at 7:30am local time. (optional)
    # yoy power rankings                  thursday afternoon at 3:00pm east coast time.
    # matchups:                           thursday evening at 7:30pm east coast time.
    # score update:                       friday, monday, and tuesday morning at 7:30am local time.
    # player monitor report:              sunday morning at 7:30am local time.
    # score update:                       sunday at 4pm, 8pm east coast time.

    sched.add_job(bot_main, 'cron', ['get_close_scores'], id='close_scores',
        day_of_week='mon', hour=18, minute=30, start_date=ff_start_date, end_date=ff_end_date,
        timezone=game_timezone, replace_existing=True)
    
    sched.add_job(bot_main, 'cron', ['get_final'], id='final',
        day_of_week='tue', hour=7, minute=30, start_date=ff_start_date, end_date=ff_end_date,
        timezone=my_timezone, replace_existing=True)
    
    sched.add_job(bot_main, 'cron', ['get_expected_win_total'], id='expected_wins',
        day_of_week='tue', hour=12, minute=00, start_date=ff_start_date, end_date=ff_end_date,
        timezone=my_timezone, replace_existing=True)
    
    sched.add_job(bot_main, 'cron', ['get_power_rankings'], id='power_rankings',
        day_of_week='tue', hour=18, minute=30, start_date=ff_start_date, end_date=ff_end_date,
        timezone=my_timezone, replace_existing=True)
    
    sched.add_job(bot_main, 'cron', ['get_standings'], id='standings',
        day_of_week='wed', hour=7, minute=30, start_date=ff_start_date, end_date=ff_end_date,
        timezone=my_timezone, replace_existing=True)
    
    if daily_waiver:
        sched.add_job(bot_main, 'cron', ['get_waiver_report'], id='waiver_report',
            day_of_week='mon, tue, thu, fri, sat, sun', hour=7, minute=31, start_date=ff_start_date, end_date=ff_end_date,
            timezone=my_timezone, replace_existing=True)
    
    if weekly_waiver:
        sched.add_job(bot_main, 'cron', ['get_waiver_report'], id='waiver_report',
            day_of_week='wed', hour=8, minute=30, start_date=ff_start_date, end_date=ff_end_date,
            timezone=my_timezone, replace_existing=True)

    sched.add_job(bot_main, 'cron', ['power_rankings_yoy'], id='power_rankings_yoy',
        day_of_week='thu', hour=15, minute=00, start_date=ff_start_date, end_date=ff_end_date,
        timezone=game_timezone, replace_existing=True)
    
    sched.add_job(bot_main, 'cron', ['get_matchups'], id='matchups',
        day_of_week='thu', hour=19, minute=30, start_date=ff_start_date, end_date=ff_end_date,
        timezone=game_timezone, replace_existing=True)
    
    sched.add_job(bot_main, 'cron', ['get_scoreboard_short'], id='scoreboard1',
        day_of_week='fri,mon', hour=7, minute=30, start_date=ff_start_date, end_date=ff_end_date,
        timezone=my_timezone, replace_existing=True)

    if monitor_report:
        sched.add_job(bot_main, 'cron', ['get_monitor'], id='monitor',
                    day_of_week='sun', hour=7, minute=30, start_date=ff_start_date, end_date=ff_end_date,
                    timezone=my_timezone, replace_existing=True)

    sched.add_job(bot_main, 'cron', ['get_scoreboard_short'], id='scoreboard2',
                  day_of_week='sun', hour='16,20', start_date=ff_start_date, end_date=ff_end_date,
                  timezone=game_timezone, replace_existing=True)

    print("Ready!")
    sched.start()



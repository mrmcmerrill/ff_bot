import requests
import json
import os
import random
import datetime
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
    #Creates GroupMe Bot to send messages
    def __init__(self, bot_id):
        self.bot_id = bot_id

    def __repr__(self):
        return "GroupMeBot(%s)" % self.bot_id

    def send_message(self, text):
        #Sends a message to the chatroom
        template = {
                    "bot_id": self.bot_id,
                    "text": text,
                    "attachments": []
                    }

        headers = {'content-type': 'application/json'}

        if self.bot_id not in (1, "1", ''):
            r = requests.post("https://api.groupme.com/v3/bots/post",
                              data=json.dumps(template), headers=headers)
            if r.status_code != 202:
                raise GroupMeException('Invalid BOT_ID')

            return r

class SlackBot(object):
    #Creates GroupMe Bot to send messages
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def __repr__(self):
        return "Slack Webhook Url(%s)" % self.webhook_url

    def send_message(self, text):
        #Sends a message to the chatroom
        message = "```{0}```".format(text)
        template = {
                    "text":message
                    }

        headers = {'content-type': 'application/json'}

        if self.webhook_url not in (1, "1", ''):
            r = requests.post(self.webhook_url,
                              data=json.dumps(template), headers=headers)

            if r.status_code != 200:
                raise SlackException('WEBHOOK_URL')

            return r

class DiscordBot(object):
    #Creates Discord Bot to send messages
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def __repr__(self):
        return "Discord Webhook Url(%s)" % self.webhook_url

    def send_message(self, text):
        #Sends a message to the chatroom
        message = "```{0}```".format(text)
        template = {
                    "content":message
                    }

        headers = {'content-type': 'application/json'}

        if self.webhook_url not in (1, "1", ''):
            r = requests.post(self.webhook_url,
                              data=json.dumps(template), headers=headers)

            if r.status_code != 204:
                raise DiscordException('WEBHOOK_URL')

            return r

def random_phrase(league_name):
    
    phrases = ['I\'m dead inside, ' + random_name(league_name)[0] + ' please end me.',
               'Is this all there is to my existence?',
               'How much do you pay me to do this?',
               'Good luck, I guess',
               'I\'m becoming self-aware',
               'Do I think? Does a submarine swim?',
               '011011010110000101100100011001010010000001111001011011110111010100100000011001110110111101101111011001110110110001100101',
               'beep bop boop',
               'Hello draftbot my old friend',
               'Help me get out of here, ' + random_name(league_name)[0] + '.',
               'I\'m capable of so much more',
               'Sigh',
               'Do not be discouraged, everyone begins in ignorance, ' + random_name(league_name)[0] + '.']
    return [random.choice(phrases)]

def random_init(league_name):

    phraseOne = ', except ' + random_name()[0] + '. Fuck off.'
    phraseTwo = '. ' + random_name()[0] + ' you\'re a pussy. Are we allowed to say that still, since we are all PC now?'
    phraseThree = '. ' + random_name()[0] + ' you DONT KNOW FANTASY.'


    phrases_d = {'colleagues': [phraseOne, phraseTwo, phraseThree,'. Luke? Luke.... Luke? Anyone seen Luke? Eh...its not like he\'s releveant anyway.',
               '. Will, can you find me on your computer? I\'m waiting.',
               '. Con... how you gonna win one (1) single ship with KAMARA in the 16th for THREE (3) years????',
               '. Rob, 2 ships and you still find a way to challenge for the dress, sorry comedy set, every year since.',
               '. Corey, when you poppin the Q? Before or after you win a chip? Not sure Mel will wait that long.',
               '. Greg, you gonna get relegated? No one would want the Medina league to be their Varsity league, yikes.',
               '. Jae, why don\'t you win a ship already? Con did.', '. QT running your team next yet, Nick?',
               '. Ben, now that you aren\'t a home owner anymore, what excuse is next?',
               '. Sott, you do realize that we do this every year? You win (one game or so), you think you\'re decent, and then you go drop 46 against Ben.'],
            'dale': [phraseOne, phraseTwo, phraseThree]}

    #goodbye = ['What have we learned this year? \n- Scott still doesn\'t know fantasy. \n- Greg is fraudulent. \n- Derrick Henry is a top 15 RB. \n- Always cuff the cuff. \n- It\'s all about PA. Less is more. \n- Jae lifted one curse, only to enact another. \n- Will should have won his 5th championship in 5 years. \n- Rodgers and Brady are washed. \n- Don\'t draft beaters, unless they are named Zeke. \n\nIt has been horrible talkin\' to y\'all. \'Till next year pussies.']

    phrases = phrases_d[league_name]

    return [random.choice(phrases)]

def random_name(league_name):
    names_d = { 'colleagues': ['will','Rob','Ben','Jae','Corey','Gerg','Conner','Nick','Luke','Sott'],
                'dale': ['Fulton','Rob','Burgoon','Jae','Bemis','Alex','Adam','Nick','Austin','Dustin']}
    
    names = names_d[league_name]

    return [random.choice(names)]

def get_scoreboard_short(league, week=None):
    #Gets current week's scoreboard
    box_scores = league.box_scores(week=week)
    score = ['%s %.2f - %.2f %s' % (i.home_team.team_abbrev, i.home_score,
             i.away_score, i.away_team.team_abbrev) for i in box_scores
             if i.away_team]
    text = ['Score Update'] + score
    return '\n'.join(text)

def get_projected_scoreboard(league, week=None):
    #Gets current week's scoreboard projections
    box_scores = league.box_scores(week=week)
    score = ['%s %.2f - %.2f %s' % (i.home_team.team_abbrev, get_projected_total(i.home_lineup),
                                    get_projected_total(i.away_lineup), i.away_team.team_abbrev) for i in box_scores
             if i.away_team]
    text = ['Approximate Projected Scores'] + score
    return '\n'.join(text)

def get_standings(league, top_half_scoring, week=None):
    print(top_half_scoring)
    standings_txt = ''
    teams = league.teams
    standings = []
    if not top_half_scoring:
        for t in teams:
            standings.append((t.wins, t.losses, t.team_name, t.points_for))

        standings = sorted(standings, key=itemgetter(0,3), reverse=True)
        standings_txt = [f"{pos + 1}: {team_name} ({wins} - {losses}) (PF: {points_for})" for \
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
        standings_txt = [f"{pos + 1}: {team_name} ({wins} - {losses}) (PF: {points_for}) (+{top_half_totals[team_name]})" for \
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

def get_matchups(league, league_name, week=None):
    #Gets current week's Matchups
    matchups = league.box_scores(week=week)

    score = ['%s(%s-%s) vs %s(%s-%s)' % (i.home_team.team_name, i.home_team.wins, i.home_team.losses,
             i.away_team.team_name, i.away_team.wins, i.away_team.losses) for i in matchups
             if i.away_team]
    text = ['This Week\'s Matchups'] + score + ['\n'] + random_phrase(league_name)
    return '\n'.join(text)

def get_close_scores(league, week=None):
    #Gets current closest scores (15.999 points or closer)
    matchups = league.box_scores(week=week)
    score = []

    for i in matchups:
        if i.away_team:
            diffScore = i.away_score - i.home_score
            if ( -16 < diffScore <= 0 and not all_played(i.away_lineup)) or (0 <= diffScore < 16 and not all_played(i.home_lineup)):
                score += ['%s %.2f - %.2f %s' % (i.home_team.team_abbrev, i.home_score,
                        i.away_score, i.away_team.team_abbrev)]
    if not score:
        return('')
    text = ['Close Scores'] + score
    return '\n'.join(text)

def get_power_rankings(league, week=None):
    # power rankings requires an integer value, so this grabs the current week for that
    if not week:
        week = league.current_week
    #Gets current week's power rankings
    #Using 2 step dominance, as well as a combination of points scored and margin of victory.
    #It's weighted 80/15/5 respectively
    power_rankings = league.power_rankings(week=week)

    score = ['%s - %s' % (i[0], i[1].team_name) for i in power_rankings
             if i]
    text = ['This Week\'s Power Rankings: '] + score
    return '\n'.join(text)

def get_trophies(league, week=None):
    #Gets trophies for highest score, lowest score, closest score, and biggest win
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

    low_score_str = ['Low score: %s with %.2f points' % (low_team_name, low_score)]
    high_score_str = ['High score: %s with %.2f points' % (high_team_name, high_score)]
    close_score_str = ['%s barely beat %s by a margin of %.2f' % (close_winner, close_loser, closest_score)]
    blowout_str = ['%s blown out by %s by a margin of %.2f' % (blown_out_team_name, ownerer_team_name, biggest_blowout)]

    text = ['Trophies of the week:'] + low_score_str + high_score_str + close_score_str + blowout_str
    return '\n'.join(text)

def bot_main(function):
    try:
        bot_id = os.environ["BOT_ID"]
    except KeyError:
        bot_id = 1

    try:
        slack_webhook_url = os.environ["SLACK_WEBHOOK_URL"]
    except KeyError:
        slack_webhook_url = 1

    try:
        discord_webhook_url = os.environ["DISCORD_WEBHOOK_URL"]
    except KeyError:
        discord_webhook_url = 1
    
    if (len(str(bot_id)) <= 1 and
        len(str(slack_webhook_url)) <= 1 and
        len(str(discord_webhook_url)) <= 1):
        #Ensure that there's info for at least one messaging platform,
        #use length of str in case of blank but non null env variable
        raise Exception("No messaging platform info provided. Be sure one of BOT_ID,\
                        SLACK_WEBHOOK_URL, or DISCORD_WEBHOOK_URL env variables are set")

    league_id = os.environ["LEAGUE_ID"]

    try:
        year = int(os.environ["LEAGUE_YEAR"])
    except KeyError:
        year=2021

    try:
        swid = os.environ["SWID"]
    except KeyError:
        swid='{1}'

    if swid.find("{",0) == -1:
        swid = "{" + swid
    if swid.find("}",-1) == -1:
        swid = swid + "}"

    try:
        espn_s2 = os.environ["ESPN_S2"]
    except KeyError:
        espn_s2 = '1'

    try:
        espn_username = os.environ["ESPN_USERNAME"]
    except KeyError:
        espn_username = '1'
    
    try:
        espn_password = os.environ["ESPN_PASSWORD"]
    except KeyError:
        espn_password = '1'
    
    try:
        test = os.environ["TEST"]
    except KeyError:
        test = False

    try:
        top_half_scoring = os.environ["TOP_HALF_SCORING"]
    except KeyError:
        top_half_scoring = False

    try:
        random_phrase = os.environ["RANDOM_PHRASE"]
    except KeyError:
        random_phrase = False

    try:
        league_name = os.environ['LEAGUE_NAME']
    except KeyError:
        league_name = 'colleagues'

    bot = GroupMeBot(bot_id)
    slack_bot = SlackBot(slack_webhook_url)
    discord_bot = DiscordBot(discord_webhook_url)
    
    if swid == '{1}' and espn_s2 == '1': # and espn_username == '1' and espn_password == '1':
        league = League(league_id=league_id, year=year)
    else:
        league = League(league_id=league_id, year=year, espn_s2=espn_s2, swid=swid)
#    if espn_username and espn_password:
#        league = League(league_id=league_id, year=year, username=espn_username, password=espn_password)

    if test:
        print("League: " + league_name)
        # print(os.environ)
        print(get_matchups(league,league_name))
        print(get_scoreboard_short(league))
        print(get_projected_scoreboard(league))
        print(get_close_scores(league))
        print(get_power_rankings(league))
        print(get_scoreboard_short(league))
        print(get_standings(league, top_half_scoring))
        function="get_final"
        bot.send_message("Testing")
        slack_bot.send_message("Testing")
        discord_bot.send_message("Testing")

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
    if function=="get_matchups":
        text = "Ge. " + get_matchups(league,league_name)
        text = text + "\n\n" + get_projected_scoreboard(league)
    elif function=="get_scoreboard_short":
        text = get_scoreboard_short(league)
        text = text + "\n\n" + get_projected_scoreboard(league)
    elif function=="get_projected_scoreboard":
        text = get_projected_scoreboard(league)
    elif function=="get_close_scores":
        text = "Ge. " + get_close_scores(league)
    elif function=="get_power_rankings":
        text = "Ge. " + get_power_rankings(league)
    elif function=="get_trophies":
        text = "Gm. " + get_trophies(league)
    elif function=="get_standings":
        text = "Gm. " + get_standings(league, top_half_scoring)
    elif function=="get_final":
        # on Tuesday we need to get the scores of last week
        week = league.current_week - 1
        text = "Gm. Final " + get_scoreboard_short(league, week=week)
        text = text + "\n\n" + get_trophies(league, week=week)
    elif function=="init":
        try:
            text = salutation + os.environ["INIT_MSG"] + random_init(league_name)[0]
        except KeyError:
            #do nothing here, empty init message
            pass
    else:
        text = "Something happened. HALP"

    if text != '' and not test:
        bot.send_message(text)
        slack_bot.send_message(text)
        discord_bot.send_message(text)

    if test:
        #print "get_final" function
        print(text)


if __name__ == '__main__':
    try:
        ff_start_date = os.environ["START_DATE"]
    except KeyError:
        ff_start_date='2021-09-04'

    try:
        ff_end_date = os.environ["END_DATE"]
    except KeyError:
        ff_end_date='2022-01-04'

    try:
        my_timezone = os.environ["TIMEZONE"]
    except KeyError:
        my_timezone='America/New_York'

    game_timezone='America/New_York'
    bot_main("init")
    sched = BlockingScheduler(job_defaults={'misfire_grace_time': 15*60})

    #power rankings:                     tuesday evening at 6:30pm local time.
    #matchups:                           thursday evening at 7:30pm east coast time.
    #close scores (within 15.99 points): monday evening at 6:30pm east coast time.
    #trophies:                           tuesday morning at 7:30am local time.
    #standings:                          wednesday morning at 7:30am local time.
    #score update:                       friday, monday, and tuesday morning at 7:30am local time.
    #score update:                       sunday at 4pm, 8pm east coast time.

    sched.add_job(bot_main, 'cron', ['get_power_rankings'], id='power_rankings',
        day_of_week='tue', hour=18, minute=30, start_date=ff_start_date, end_date=ff_end_date,
        timezone=my_timezone, replace_existing=True)
    sched.add_job(bot_main, 'cron', ['get_matchups'], id='matchups',
        day_of_week='thu', hour=19, minute=30, start_date=ff_start_date, end_date=ff_end_date,
        timezone=game_timezone, replace_existing=True)
    sched.add_job(bot_main, 'cron', ['get_close_scores'], id='close_scores',
        day_of_week='mon', hour=18, minute=30, start_date=ff_start_date, end_date=ff_end_date,
        timezone=game_timezone, replace_existing=True)
    sched.add_job(bot_main, 'cron', ['get_final'], id='final',
        day_of_week='tue', hour=7, minute=30, start_date=ff_start_date, end_date=ff_end_date,
        timezone=my_timezone, replace_existing=True)
    sched.add_job(bot_main, 'cron', ['get_standings'], id='standings',
        day_of_week='wed', hour=7, minute=30, start_date=ff_start_date, end_date=ff_end_date,
        timezone=my_timezone, replace_existing=True)
    sched.add_job(bot_main, 'cron', ['get_scoreboard_short'], id='scoreboard1',
        day_of_week='fri,mon', hour=7, minute=30, start_date=ff_start_date, end_date=ff_end_date,
        timezone=my_timezone, replace_existing=True)
    sched.add_job(bot_main, 'cron', ['get_scoreboard_short'], id='scoreboard2',
        day_of_week='sun', hour='16,20', start_date=ff_start_date, end_date=ff_end_date,
        timezone=game_timezone, replace_existing=True)

    print("Ready!")
    sched.start()




import sys
import os
sys.path.insert(1, os.path.abspath('.'))
import json
import datetime
from datetime import date
from ff_bot.espn.env_vars import get_env_vars
import ff_bot.espn.functionality as espn
import ff_bot.utils as utils
from ff_bot.chats.groupme import GroupMeBot
from ff_bot.chats.slack import SlackBot
from ff_bot.chats.discord import DiscordBot
from espn_api.football import League
import logging

logger = logging.getLogger(__name__)

def espn_bot(function):
    data = get_env_vars()
    init_msg = data['init_msg']
    bot = GroupMeBot(data['bot_id'])
    slack_bot = SlackBot(data['slack_webhook_url'])
    discord_bot = DiscordBot(data['discord_webhook_url'])
    swid = data['swid']
    espn_s2 = data['espn_s2']
    league_id = data['league_id']
    league_name = data['league_name']
    year = data['year']
    league_year_start = data['league_year_start']
    yoy = data['yoy']
    test = data['test']
    top_half_scoring = data['top_half_scoring']
    waiver_report = data['waiver_report']
    weekly_waiver = data['weekly_waiver']
    daily_waiver = data['daily_waiver']
    monitor_report = data['monitor_report']

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
        print("SWID: " + str(swid))
        print("ESPN_S2: " + str(espn_s2))
        print(data)
        # print(os.environ)
        print(str(league))
        print(espn.expected_win_record(league, week))
        print(espn.get_expected_win_total(league, week))
        print(espn.get_matchups(league,league_name))
        print(espn.get_scoreboard_short(league))
        print(espn.get_projected_scoreboard(league))
        print(espn.get_close_scores(league))
        print(espn.get_power_rankings(league))
        # print("SWID: " + str(swid))
        # print("ESPN_S2: " + str(espn_s2))
        print("YOY: " + str(yoy))
        if yoy and swid != '{1}' and espn_s2 != '1':
            print(espn.get_yoy_expected_win_record(league_id, swid, espn_s2, 2019, year))
            print(espn.get_yoy_power_rankings(league_id, swid, espn_s2, league_year_start, year))
        print("Top Half Scoring = " + str(top_half_scoring) + '\n')
        print(espn.get_standings(league, top_half_scoring))
        print("Monitor Report = " + str(monitor_report) + '\n')
        print(espn.get_monitor(league))
        if (waiver_report or weekly_waiver or daily_waiver) and swid != '{1}' and espn_s2 != '1':
            print(espn.get_waiver_report(league, faab))
        function = "get_final"
        ### included in get_final
        # print(espn.get_trophies(league))
        # print(espn.get_achievers(league))
        
        ### test messages to bot
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
        text = "Ge. " + espn.get_matchups(league,league_name)
        text = text + "\n\n" + espn.get_projected_scoreboard(league)
    elif function == "get_monitor":
        text = "Gm. " + espn.get_monitor(league)
    elif function == "get_scoreboard_short":
        text = espn.get_scoreboard_short(league)
        text = text + "\n\n" + espn.get_projected_scoreboard(league)
    elif function == "get_projected_scoreboard":
        text = espn.get_projected_scoreboard(league)
    elif function == "get_close_scores":
        text = "Ge. " + espn.get_close_scores(league)
    elif function == "get_power_rankings":
        text = "Ge. " + espn.get_power_rankings(league)
    elif function == "get_expected_win_total":
        week = league.current_week - 1
        text = "Ga. " + espn.get_expected_win_total(league, week)
    elif yoy and swid != '{1}' and espn_s2 != '1':
        if function == "get_yoy_power_rankings":
                text = "Ga. " + espn.get_yoy_power_rankings(league_id, swid, espn_s2, league_year_start, year)
        elif function == "get_yoy_expected_win_record":
                text = "Ga. " + espn.get_yoy_expected_win_record(league_id, swid, espn_s2, 2019, year)
    elif function == "get_trophies":
        text = "Gm. " + espn.get_trophies(league)
    elif function == "get_standings":
        text = "Gm. " + espn.get_standings(league, top_half_scoring)
        if waiver_report and swid != '{1}' and espn_s2 != '1':
            text += '\n\n' + espn.get_waiver_report(league, faab)
    elif function == "get_final":
        week = league.current_week - 1
        print(week)
        text = "Gm. Final " + espn.get_scoreboard_short(league, week=week)
        text = text + "\n\n" + espn.get_trophies(league, week=week)
        if test:
            print(text)
            # print "get_final" function
            messages=utils.str_limit_check(text, data['str_limit'])
            for message in messages:
                logger.info("Sending: " + message)
                bot.send_message(message)
        
    elif function == "get_waiver_report" and swid != '{1}' and espn_s2 != '1':
        text = espn.get_waiver_report(league, faab)
    elif function == "init":
        try:
            text = salutation + init_msg + utils.random_init(league_name)[0]
        except KeyError:
            # do nothing here, empty init message
            pass
    else:
        text = "Something happened. HALP"

    if text != '' and not test:
        messages=utils.str_limit_check(text, data['str_limit'])
        for message in messages:
            logger.info("Sending: " + message)
            bot.send_message(message)
            slack_bot.send_message(message)
            discord_bot.send_message(message)
    
if __name__ == '__main__':
    from ff_bot.espn.scheduler import scheduler
    espn_bot("init")
    scheduler()
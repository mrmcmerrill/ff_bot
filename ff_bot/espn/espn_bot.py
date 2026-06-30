"""Entry point that dispatches a named report and posts it to the configured chat platforms."""

import datetime
import logging

from ff_bot.espn.env_vars import get_env_vars
import ff_bot.espn.functionality as espn
import ff_bot.utils as utils
from ff_bot.chats.groupme import GroupMeBot
from ff_bot.chats.slack import SlackBot
from ff_bot.chats.discord import DiscordBot
from espn_api.football import League

logger = logging.getLogger(__name__)


def espn_bot(function):
    """Run the report named by `function`, then send the result to GroupMe/Slack/Discord.

    `function` is one of the scheduler's report names (e.g. "get_matchups", "get_final").
    Each report is prefixed with a time-of-day salutation. In TEST mode every report is
    printed to stdout instead of being posted, and the dispatch is forced to "get_final".
    """
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

    # Public leagues need no credentials; private leagues require SWID + espn_s2 cookies.
    if swid == '{1}' or espn_s2 == '1':
        league = League(league_id=league_id, year=year)
    else:
        league = League(league_id=league_id, year=year, espn_s2=espn_s2, swid=swid)

    # Bail out once the season is over (current scoring period is past the last matchup week).
    if league.scoringPeriodId > len(league.settings.matchup_periods):
        print("Not in active season")
        return

    faab = league.settings.faab

    if test:
        week = league.current_week - 1
        print(f"League: {league_name}")
        print(f"SWID: {swid}")
        print(f"ESPN_S2: {espn_s2}")
        print(data)
        print(str(league))
        print(espn.expected_win_record(league, week))
        print(espn.get_expected_win_total(league, week))
        print(espn.get_matchups(league, league_name))
        print(espn.get_scoreboard_short(league))
        print(espn.get_projected_scoreboard(league))
        print(espn.get_close_scores(league))
        print(espn.get_power_rankings(league))
        print(espn.optimal_team_scores(league, full_report=True))
        print(f"YOY: {yoy}")
        if yoy and swid != '{1}' and espn_s2 != '1':
            # Expected wins is floored at 2019: ESPN box-score data isn't usable in this
            # format before then. Power rankings work further back, so they use league_year_start.
            print(espn.get_yoy_expected_win_record(league_id, swid, espn_s2, 2019, year))
            print(espn.get_yoy_power_rankings(league_id, swid, espn_s2, league_year_start, year))
        print(f"Top Half Scoring = {top_half_scoring}\n")
        print(espn.get_standings(league, top_half_scoring))
        print(f"Monitor Report = {monitor_report}\n")
        print(espn.get_monitor(league))
        if (waiver_report or weekly_waiver or daily_waiver) and swid != '{1}' and espn_s2 != '1':
            print(espn.get_waiver_report(league, faab))
        function = "get_final"

    currentHour = datetime.datetime.now().hour
    if 6 < currentHour < 17:
        salutation = "Gm. "
    elif 17 <= currentHour < 22:
        salutation = "Ga. "
    else:
        salutation = "Ge. "

    text = ''

    if function == "get_matchups":
        text = f"Ge. {espn.get_matchups(league, league_name)}"
        text += f"\n\n{espn.get_projected_scoreboard(league)}"
    elif function == "get_monitor":
        text = f"Gm. {espn.get_monitor(league)}"
    elif function == "get_scoreboard_short":
        text = espn.get_scoreboard_short(league)
        text += f"\n\n{espn.get_projected_scoreboard(league)}"
    elif function == "get_projected_scoreboard":
        text = espn.get_projected_scoreboard(league)
    elif function == "get_close_scores":
        text = f"Ge. {espn.get_close_scores(league)}"
    elif function == "get_power_rankings":
        text = f"Ge. {espn.get_power_rankings(league)}"
    elif function == "get_expected_win_total":
        week = league.current_week - 1
        text = f"Ga. {espn.get_expected_win_total(league, week)}"
    elif function == "get_yoy_power_rankings":
        if yoy and swid != '{1}' and espn_s2 != '1':
            text = f"Ga. {espn.get_yoy_power_rankings(league_id, swid, espn_s2, league_year_start, year)}"
    elif function == "get_yoy_expected_win_record":
        if yoy and swid != '{1}' and espn_s2 != '1':
            # 2019 floor: ESPN box-score data isn't usable in this format before 2019.
            text = f"Ga. {espn.get_yoy_expected_win_record(league_id, swid, espn_s2, 2019, year)}"
    elif function == "get_trophies":
        text = f"Gm. {espn.get_trophies(league)}"
    elif function == "get_optimized_linuep_report":
        week = league.current_week - 1
        text = f"Gm. {espn.optimal_team_scores(league, week, full_report=True)}"
    elif function == "get_standings":
        text = f"Gm. {espn.get_standings(league, top_half_scoring)}"
        if waiver_report and swid != '{1}' and espn_s2 != '1':
            text += f"\n\n{espn.get_waiver_report(league, faab)}"
    elif function == "get_final":
        week = league.current_week - 1
        text = f"Gm. Final {espn.get_scoreboard_short(league, week=week)}"
        text += f"\n\n{espn.get_trophies(league, week=week)}"
        if test:
            print(text)
            messages = utils.str_limit_check(text, data['str_limit'])
            for message in messages:
                logger.info(f"Sending: {message}")
                bot.send_message(message)
    elif function == "get_waiver_report" and swid != '{1}' and espn_s2 != '1':
        text = espn.get_waiver_report(league, faab)
    elif function == "init":
        try:
            text = salutation + init_msg + utils.random_init(league_name)[0]
        except KeyError:
            pass
    else:
        text = "Something happened. HALP"

    # Post to every configured platform, splitting into chunks if over the char limit.
    if text != '' and not test:
        messages = utils.str_limit_check(text, data['str_limit'])
        for message in messages:
            logger.info(f"Sending: {message}")
            bot.send_message(message)
            slack_bot.send_message(message)
            discord_bot.send_message(message)


if __name__ == '__main__':
    from ff_bot.espn.scheduler import scheduler
    espn_bot("init")
    scheduler()

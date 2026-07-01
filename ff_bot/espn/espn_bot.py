"""Entry point that dispatches a named report and posts it to the configured chat platforms.

Reports come from one of two providers depending on data['provider']: the live ESPN
path (ff_bot.espn.functionality, driven by an espn_api League) or the live Sleeper path
(ff_bot.sleeper.functionality, driven by a SleeperClient). The all-time/YoY reports and
the init message are provider-agnostic and handled once, before the provider branch.
"""

import datetime
import logging

from ff_bot.espn.env_vars import get_env_vars
import ff_bot.espn.functionality as espn
import ff_bot.sleeper.functionality as sleeper
from ff_bot.sleeper.client import SleeperClient
import ff_bot.common.history as history
import ff_bot.utils as utils
from ff_bot.chats.groupme import GroupMeBot
from ff_bot.chats.slack import SlackBot
from ff_bot.chats.discord import DiscordBot
from espn_api.football import League

logger = logging.getLogger(__name__)


def _salutation():
    """Time-of-day greeting prefix used by the init message."""
    hour = datetime.datetime.now().hour
    if 6 < hour < 17:
        return "Gm. "
    if 17 <= hour < 22:
        return "Ga. "
    return "Ge. "


def _init_text(data):
    """Season-start greeting, or '' if no init message is configured."""
    try:
        return _salutation() + data['init_msg'] + utils.random_init(data['league_name'])[0]
    except KeyError:
        return ''


# -- ESPN provider ---------------------------------------------------------

def _build_espn_league(data):
    """Construct an espn_api League (credentialed for private leagues)."""
    swid, espn_s2 = data['swid'], data['espn_s2']
    if swid == '{1}' or espn_s2 == '1':
        return League(league_id=data['league_id'], year=data['year'])
    return League(league_id=data['league_id'], year=data['year'], espn_s2=espn_s2, swid=swid)


def _espn_in_season(league):
    """False once the season is over (current scoring period past the last matchup week)."""
    return league.scoringPeriodId <= len(league.settings.matchup_periods)


def _espn_report(function, data):
    """Build the text for a report from the live ESPN league."""
    league = _build_espn_league(data)
    if not _espn_in_season(league):
        print("Not in active season")
        return ''

    league_name = data['league_name']
    top_half_scoring = data['top_half_scoring']
    waiver_report = data['waiver_report']
    swid, espn_s2 = data['swid'], data['espn_s2']
    faab = league.settings.faab
    credentialed = swid != '{1}' and espn_s2 != '1'

    if function == "get_matchups":
        return (f"Ge. {espn.get_matchups(league, league_name)}"
                f"\n\n{espn.get_projected_scoreboard(league)}")
    if function == "get_monitor":
        return f"Gm. {espn.get_monitor(league)}"
    if function == "get_scoreboard_short":
        return f"{espn.get_scoreboard_short(league)}\n\n{espn.get_projected_scoreboard(league)}"
    if function == "get_projected_scoreboard":
        return espn.get_projected_scoreboard(league)
    if function == "get_close_scores":
        return f"Ge. {espn.get_close_scores(league)}"
    if function == "get_power_rankings":
        return f"Ge. {espn.get_power_rankings(league)}"
    if function == "get_expected_win_total":
        return f"Ga. {espn.get_expected_win_total(league, league.current_week - 1)}"
    if function == "get_trophies":
        return f"Gm. {espn.get_trophies(league)}"
    if function == "get_optimized_linuep_report":
        return f"Gm. {espn.optimal_team_scores(league, league.current_week - 1, full_report=True)}"
    if function == "get_standings":
        text = f"Gm. {espn.get_standings(league, top_half_scoring)}"
        if waiver_report and credentialed:
            text += f"\n\n{espn.get_waiver_report(league, faab)}"
        return text
    if function == "get_final":
        week = league.current_week - 1
        return (f"Gm. Final {espn.get_scoreboard_short(league, week=week)}"
                f"\n\n{espn.get_trophies(league, week=week)}")
    if function == "get_waiver_report":
        return espn.get_waiver_report(league, faab) if credentialed else ''
    return "Something happened. HALP"


# -- Sleeper provider ------------------------------------------------------

def _sleeper_report(function, data):
    """Build the text for a report from the live Sleeper league.

    Current-week reports use the live NFL week; season-cumulative reports (power
    rankings, expected wins, trophies, final, waivers) use the last completed week.
    """
    client = SleeperClient(data['sleeper_league_id'])
    current = client.current_week()
    if current <= 0:
        print("Not in active season")
        return ''

    league_name = data['league_name']
    top_half_scoring = data['top_half_scoring']
    waiver_report = data['waiver_report']
    completed = max(current - 1, 1)

    if function == "get_matchups":
        return f"Ge. {sleeper.get_matchups(client, league_name, current)}"
    if function == "get_monitor":
        return f"Gm. {sleeper.get_monitor(client, current)}"
    if function == "get_scoreboard_short":
        return sleeper.get_scoreboard_short(client, current)
    if function == "get_projected_scoreboard":
        return ''  # Sleeper has no projections
    if function == "get_close_scores":
        return f"Ge. {sleeper.get_close_scores(client, current)}"
    if function == "get_power_rankings":
        return f"Ge. {sleeper.get_power_rankings(client, completed)}"
    if function == "get_expected_win_total":
        return f"Ga. {sleeper.get_expected_win_total(client, completed)}"
    if function == "get_trophies":
        return f"Gm. {sleeper.get_trophies(client, completed)}"
    if function == "get_optimized_linuep_report":
        return f"Gm. {sleeper.optimal_team_scores(client, completed, full_report=True)}"
    if function == "get_standings":
        text = f"Gm. {sleeper.get_standings(client, top_half_scoring)}"
        if waiver_report:
            text += f"\n\n{sleeper.get_waiver_report(client, completed)}"
        return text
    if function == "get_final":
        return f"Gm. {sleeper.get_final(client, completed)}"
    if function == "get_waiver_report":
        return sleeper.get_waiver_report(client, completed)
    return "Something happened. HALP"


# -- dispatch --------------------------------------------------------------

def _report_text(function, data):
    """Route a report name to the right provider (or the shared provider-agnostic reports)."""
    league_name = data['league_name']

    if function == "init":
        return _init_text(data)
    if function == "get_yoy_power_rankings":
        return f"Ga. {history.get_all_time_power_rankings(league_name)}" if data['yoy'] else ''
    if function == "get_yoy_expected_win_record":
        return f"Ga. {history.get_all_time_expected_wins(league_name)}" if data['yoy'] else ''

    if data['provider'] == 'sleeper':
        return _sleeper_report(function, data)
    return _espn_report(function, data)


def _print_test_report(data):
    """Print every available report for the configured provider without sending anything."""
    league_name = data['league_name']
    print(f"League: {league_name} ({data['provider']})")
    print(data)

    if data['provider'] == 'sleeper':
        client = SleeperClient(data['sleeper_league_id'])
        current = client.current_week()
        week = max(current - 1, 1) if current > 0 else client.regular_season_weeks()
        print(sleeper.get_scoreboard_short(client, week))
        print(sleeper.get_matchups(client, league_name, week))
        print(sleeper.get_power_rankings(client, week))
        print(sleeper.get_expected_win_total(client, week))
        print(sleeper.get_standings(client, data['top_half_scoring']))
        print(sleeper.optimal_team_scores(client, week, full_report=True))
        print(sleeper.get_trophies(client, week))
        print(sleeper.get_monitor(client, week))
        print(sleeper.get_waiver_report(client, week))
    else:
        league = _build_espn_league(data)
        if not _espn_in_season(league):
            print("Not in active season")
            return
        week = league.current_week - 1
        print(espn.get_expected_win_total(league, week))
        print(espn.get_matchups(league, league_name))
        print(espn.get_scoreboard_short(league))
        print(espn.get_projected_scoreboard(league))
        print(espn.get_close_scores(league))
        print(espn.get_power_rankings(league))
        print(espn.optimal_team_scores(league, full_report=True))
        print(espn.get_standings(league, data['top_half_scoring']))
        print(espn.get_monitor(league))

    if data['yoy']:
        print(history.get_all_time_power_rankings(league_name))
        print(history.get_all_time_expected_wins(league_name))


def espn_bot(function):
    """Run the report named by `function`, then send the result to GroupMe/Slack/Discord.

    `function` is one of the scheduler's report names (e.g. "get_matchups", "get_final").
    In TEST mode every report is printed to stdout instead of being posted.
    """
    data = get_env_vars()
    bot = GroupMeBot(data['bot_id'])
    slack_bot = SlackBot(data['slack_webhook_url'])
    discord_bot = DiscordBot(data['discord_webhook_url'])

    if data['test']:
        _print_test_report(data)
        return

    text = _report_text(function, data)

    # Post to every configured platform, splitting into chunks if over the char limit.
    if text:
        for message in utils.str_limit_check(text, data['str_limit']):
            logger.info(f"Sending: {message}")
            bot.send_message(message)
            slack_bot.send_message(message)
            discord_bot.send_message(message)


if __name__ == '__main__':
    from ff_bot.espn.scheduler import scheduler
    espn_bot("init")
    scheduler()

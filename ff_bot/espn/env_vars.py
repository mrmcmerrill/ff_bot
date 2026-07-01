import os
import ff_bot.utils as utils


def get_env_vars():
    """Read all bot configuration from environment variables into a single dict.

    PROVIDER ('espn' or 'sleeper', default 'espn') selects which platform the current
    live season runs on. An ESPN league requires LEAGUE_ID; a Sleeper league requires
    SLEEPER_LEAGUE_ID. (All-time reports read frozen snapshots regardless of provider.)

    The str_limit is tuned to the active messaging platform (GroupMe 1000, Discord 3000,
    Slack 40000), and at least one of BOT_ID, SLACK_WEBHOOK_URL, or DISCORD_WEBHOOK_URL
    must be set or an exception is raised.
    """
    data = {}

    data['league_year_start'] = int(os.environ.get("LEAGUE_YEAR_START", 2017))
    data['yoy'] = utils.str_to_bool(os.environ.get("YOY", "false"))
    data['ff_start_date'] = os.environ.get("START_DATE", "2023-09-07")
    data['ff_end_date'] = os.environ.get("END_DATE", "2024-01-09")
    data['my_timezone'] = os.environ.get("TIMEZONE", "America/New_York")
    data['daily_waiver'] = utils.str_to_bool(os.environ.get("DAILY_WAIVER", "false"))
    data['weekly_waiver'] = utils.str_to_bool(os.environ.get("WEEKLY_WAIVER", "false"))
    data['monitor_report'] = utils.str_to_bool(os.environ.get("MONITOR_REPORT", "false"))

    str_limit = 40000  # slack char limit

    bot_id = os.environ.get("BOT_ID", "1")
    if bot_id != "1":
        str_limit = 1000

    slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "1")
    discord_webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "1")
    if discord_webhook_url != "1":
        str_limit = 3000

    if len(bot_id) <= 1 and len(slack_webhook_url) <= 1 and len(discord_webhook_url) <= 1:
        raise Exception(
            "No messaging platform info provided. Be sure one of "
            "BOT_ID, SLACK_WEBHOOK_URL, or DISCORD_WEBHOOK_URL env variables are set"
        )

    data['str_limit'] = str_limit
    data['bot_id'] = bot_id
    data['slack_webhook_url'] = slack_webhook_url
    data['discord_webhook_url'] = discord_webhook_url

    # `or "espn"` (not a .get default) so an empty PROVIDER="" — which the deploy script
    # passes for leagues that don't set one — still falls back to the default.
    provider = (os.environ.get("PROVIDER") or "espn").lower()
    if provider not in ("espn", "sleeper"):
        raise Exception(f"Unknown PROVIDER '{provider}'; expected 'espn' or 'sleeper'")
    data['provider'] = provider

    league_id = os.environ.get("LEAGUE_ID", "")
    sleeper_league_id = os.environ.get("SLEEPER_LEAGUE_ID", "")
    if provider == "espn" and not league_id:
        raise Exception("PROVIDER=espn requires the LEAGUE_ID env variable")
    if provider == "sleeper" and not sleeper_league_id:
        raise Exception("PROVIDER=sleeper requires the SLEEPER_LEAGUE_ID env variable")
    data['league_id'] = league_id
    data['sleeper_league_id'] = sleeper_league_id

    data['league_name'] = os.environ.get("LEAGUE_NAME", "colleagues")
    data['year'] = int(os.environ.get("LEAGUE_YEAR", 2023))

    # ESPN's SWID cookie is expected wrapped in braces; add them if the user omitted them.
    swid = os.environ.get("SWID", "{1}")
    if not swid.startswith("{"):
        swid = "{" + swid
    if not swid.endswith("}"):
        swid = swid + "}"
    data['swid'] = swid

    data['espn_s2'] = os.environ.get("ESPN_S2", "1")
    data['test'] = utils.str_to_bool(os.environ.get("TEST", "false"))
    data['top_half_scoring'] = utils.str_to_bool(os.environ.get("TOP_HALF_SCORING", "false"))
    data['random_phrase'] = utils.str_to_bool(os.environ.get("RANDOM_PHRASE", "false"))
    data['waiver_report'] = utils.str_to_bool(os.environ.get("WAIVER_REPORT", "false"))
    data['init_msg'] = os.environ.get("INIT_MSG", "")

    return data

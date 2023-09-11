from apscheduler.schedulers.blocking import BlockingScheduler
from ff_bot.espn.espn_bot import espn_bot
from ff_bot.espn.env_vars import get_env_vars

def scheduler():
    data = get_env_vars()
    game_timezone = 'America/New_York'
    sched = BlockingScheduler(job_defaults={'misfire_grace_time': 15*60})
    ff_start_date = data['ff_start_date']
    ff_end_date = data['ff_end_date']
    my_timezone = data['my_timezone']

    # close scores (within 15.99 points): monday evening at 6:30pm east coast time.
    # trophies:                           tuesday morning at 7:30am local time.
    # optimized lineups                   tuesday morning at 11:30a local time.
    # expected wins total:                tuesday afternoon at 12:00pm local time.
    # power rankings:                     tuesday evening at 6:30pm local time.
    # standings:                          wednesday morning at 7:30am local time.
    # waiver report:                      wednesday morning at 7:30am local time. (optional)                   
    # yoy expected wins:                  thursday afternoon at 12:00pm east coast time
    # yoy power rankings:                 thursday afternoon at 3:00pm east coast time.
    # matchups:                           thursday evening at 7:30pm east coast time.
    # score update:                       friday, monday, and tuesday morning at 7:30am local time.
    # player monitor report:              sunday morning at 7:30am local time.
    # score update:                       sunday at 4pm, 8pm east coast time.

    sched.add_job(espn_bot, 'cron', ['get_close_scores'], id='close_scores',
                  day_of_week='mon', hour=18, minute=30, start_date=ff_start_date, end_date=ff_end_date,
                  timezone=game_timezone, replace_existing=True)
    
    sched.add_job(espn_bot, 'cron', ['get_final'], id='final',
                  day_of_week='tue', hour=7, minute=30, start_date=ff_start_date, end_date=ff_end_date,
                  timezone=my_timezone, replace_existing=True)
    
    sched.add_job(espn_bot, 'cron', ['get_optimized_linuep_report'], id='optimized_linup',
                  day_of_week='tue', hour=11, minute=30, start_date=ff_start_date, end_date=ff_end_date,
                  timezone=my_timezone, replace_existing=True)
    
    sched.add_job(espn_bot, 'cron', ['get_expected_win_total'], id='expected_wins',
                  day_of_week='tue', hour=12, minute=00, start_date=ff_start_date, end_date=ff_end_date,
                  timezone=my_timezone, replace_existing=True)
    
    sched.add_job(espn_bot, 'cron', ['get_power_rankings'], id='power_rankings',
                  day_of_week='tue', hour=18, minute=30, start_date=ff_start_date, end_date=ff_end_date,
                  timezone=my_timezone, replace_existing=True)
    
    sched.add_job(espn_bot, 'cron', ['get_standings'], id='standings',
                  day_of_week='wed', hour=7, minute=30, start_date=ff_start_date, end_date=ff_end_date,
                  timezone=my_timezone, replace_existing=True)
    
    if data['daily_waiver']:
        sched.add_job(espn_bot, 'cron', ['get_waiver_report'], id='waiver_report',
                      day_of_week='mon, tue, thu, fri, sat, sun', hour=7, minute=31, start_date=ff_start_date, end_date=ff_end_date,
                      timezone=my_timezone, replace_existing=True)
    
    if data['weekly_waiver']:
        sched.add_job(espn_bot, 'cron', ['get_waiver_report'], id='waiver_report',
                      day_of_week='wed', hour=8, minute=30, start_date=ff_start_date, end_date=ff_end_date,
                      timezone=my_timezone, replace_existing=True)

    if data['yoy']:
        sched.add_job(espn_bot, 'cron', ['get_yoy_expected_win_record'], id='yoy_expected_win_record',
                      day_of_week='thu', hour=12, minute=00, start_date=ff_start_date, end_date=ff_end_date,
                      timezone=game_timezone, replace_existing=True)

        sched.add_job(espn_bot, 'cron', ['get_yoy_power_rankings'], id='yoy_power_rankings',
                      day_of_week='thu', hour=15, minute=00, start_date=ff_start_date, end_date=ff_end_date,
                      timezone=game_timezone, replace_existing=True)
    
    sched.add_job(espn_bot, 'cron', ['get_matchups'], id='matchups',
                  day_of_week='thu', hour=19, minute=30, start_date=ff_start_date, end_date=ff_end_date,
                  timezone=game_timezone, replace_existing=True)
    
    sched.add_job(espn_bot, 'cron', ['get_scoreboard_short'], id='scoreboard1',
                  day_of_week='fri,mon', hour=7, minute=30, start_date=ff_start_date, end_date=ff_end_date,
                  timezone=my_timezone, replace_existing=True)

    if data['monitor_report']:
        sched.add_job(espn_bot, 'cron', ['get_monitor'], id='monitor',
                      day_of_week='sun', hour=7, minute=30, start_date=ff_start_date, end_date=ff_end_date,
                      timezone=my_timezone, replace_existing=True)

    sched.add_job(espn_bot, 'cron', ['get_scoreboard_short'], id='scoreboard2',
                  day_of_week='sun', hour='16,20', start_date=ff_start_date, end_date=ff_end_date,
                  timezone=game_timezone, replace_existing=True)

    print("Ready!")
    sched.start()
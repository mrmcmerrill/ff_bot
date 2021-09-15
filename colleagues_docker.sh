source ./colleagues_env
docker run --name colleagues_rankings_bot -e "LEAGUE_ID=$LEAGUE_ID" -e "INIT_MSG=$INIT_MSG" -e "LEAGUE_YEAR=$LEAGUE_YEAR" -e "BOT_ID=$BOT_ID" -dit mchome/ff_bot:colleagues

source ./colleagues_env
sudo docker stop colleagues-rankings-bot
sudo docker rm colleagues-rankings-bot
sudo docker run --name colleagues-rankings-bot -e "LEAGUE_ID=$LEAGUE_ID" -e "INIT_MSG=$INIT_MSG" -e "LEAGUE_YEAR=$LEAGUE_YEAR" -e "BOT_ID=$BOT_ID" -dit mchome/ff_bot:colleagues

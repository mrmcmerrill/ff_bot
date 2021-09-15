environ=$1
source ./ff-bot_env
THIS_BOT_ID="${environ}_BOT_ID"
THIS_LEAGUE_ID="${environ}_LEAGUE_ID"

if $environ eq "test"; then
  TEST=True
else
  TEST=False
fi

# Test pointer variables
# echo $THIS_BOT_ID
# echo ${!THIS_BOT_ID}

sudo docker stop ${environ}-rankings-bot
sudo docker rm ${environ}-rankings-bot
sudo docker run --name test-rankings-bot -e "LEAGUE_ID=${!THIS_LEAGUE_ID}" -e "INIT_MSG=$INIT_MSG" -e "LEAGUE_YEAR=$LEAGUE_YEAR" -e "BOT_ID=${!THIS_BOT_ID}" -e "TEST=$TEST" -e "TOP_HALF_SCORING=$TOP_HALF_SCORING" -dit mchome/ff_bot:${environ}


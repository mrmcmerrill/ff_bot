environ=$1

source ./ff-bot_env
THIS_BOT_ID="${environ}_BOT_ID"
THIS_LEAGUE_ID="${environ}_LEAGUE_ID"

if [[ "$environ" == "test" ]]; then
  TEST=True
  LEAGUE_NAME="$2"
  THIS_LEAGUE_ID="${LEAGUE_NAME}_LEAGUE_ID"
  IMAGE_TAG="test"
else
  TEST=
  LEAGUE_NAME=$environ
  IMAGE_TAG="latest"
fi

# Test pointer variables
# echo $THIS_BOT_ID
# echo ${!THIS_BOT_ID}

sudo docker stop ${environ}-rankings-bot
sudo docker rm ${environ}-rankings-bot
sudo docker run -dit --name ${environ}-rankings-bot \
	-e "LEAGUE_NAME=$LEAGUE_NAME" \
	-e "LEAGUE_ID=${!THIS_LEAGUE_ID}" \
	-e "INIT_MSG=$INIT_MSG" \
	-e "LEAGUE_YEAR=$LEAGUE_YEAR" \
   	-e "BOT_ID=${!THIS_BOT_ID}" \
	-e "TEST=$TEST" \
	mchome/ff_bot:$IMAGE_TAG

# env

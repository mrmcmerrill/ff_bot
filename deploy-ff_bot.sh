usage() { echo "Usage: $0 [-l colleagues|dale] [-t]" 1>&2; exit 1; }

while getopts "l:t" option; do
   case $option in
      l) # Enter an league
        LEAGUE_NAME=$OPTARG
        environ=$OPTARG
        ;;
      t) # if test is true
        test="true"
        ;;
      *) # display Help
        usage
        ;;
        
   esac
done

source ./ff_bot-env

if [[ "$test" == "true" ]]; then
  environ="test"
  TEST=True
  THIS_LEAGUE_ID="${LEAGUE_NAME}_LEAGUE_ID"
  THIS_LEAGUE_YEAR_START="${LEAGUE_NAME}_LEAGUE_YEAR_START"
  THIS_YOY="${LEAGUE_NAME}_YOY"
  THIS_SWID="${LEAGUE_NAME}_SWID"
  THIS_ESPN_S2="${LEAGUE_NAME}_ESPN_S2"
  IMAGE_TAG="test"
else
  environ=$LEAGUE_NAME
  TEST=
  IMAGE_TAG="latest"
fi

THIS_BOT_ID="${environ}_BOT_ID"
THIS_LEAGUE_ID="${LEAGUE_NAME}_LEAGUE_ID"
THIS_LEAGUE_YEAR_START="${LEAGUE_NAME}_LEAGUE_YEAR_START"
THIS_YOY="${LEAGUE_NAME}_YOY"
THIS_SWID="${LEAGUE_NAME}_SWID"
THIS_ESPN_S2="${LEAGUE_NAME}_ESPN_S2"

# Test pointer variables
# echo $THIS_BOT_ID
# echo ${!THIS_BOT_ID}
DOCKER_CONTAINER=`docker ps -a |grep "${environ}-rankings-bot" |awk -F " " '{print $1}'`
TEST_DOCKER_CONTAINER=`docker ps -a |grep "test-rankings-bot"| awk -F " " '{print $1}'

if [[ "$test" == "true" ] && [ -z "${$TEST_DOCKER_CONTAINER}" ]]; then
  sudo docker stop test-rankings-bot
  sudo docker rm test-rankings-bot
elif [[ -z "${DOCKER_CONTAINER}" ] && [ "$test" != "true" ]]; then
  sudo docker stop ${environ}-rankings-bot
  sudo docker rm ${environ}-rankings-bot
fi

sudo docker run -dit --name ${environ}-rankings-bot \
	-e "LEAGUE_NAME=$LEAGUE_NAME" \
	-e "LEAGUE_ID=${!THIS_LEAGUE_ID}" \
	-e "INIT_MSG=$INIT_MSG" \
	-e "LEAGUE_YEAR=$LEAGUE_YEAR" \
  -e "START_DATE=$START_DATE" \
  -e "END_DATE=$END_DATE" \
  -e "BOT_ID=${!THIS_BOT_ID}" \
  -e "TEST=$TEST" \
  -e "LEAGUE_YEAR_START=${!THIS_LEAGUE_YEAR_START}" \
  -e "YOY=${!THIS_YOY}" \
  -e "SWID=${!THIS_SWID}" \
  -e "ESPN_S2=${!THIS_ESPN_S2}" \
	mchome/ff_bot:$IMAGE_TAG

#env

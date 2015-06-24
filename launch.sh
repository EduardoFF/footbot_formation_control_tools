# launches the classic rnp scenario
# params: ids of robots

#if [[ !"$EXP_TIME" ]]; then
  #EXP_TIME=1000
#fi
WAIT_FOR_INPUT=true
MYIP=$(ip addr | grep inet | grep wlan | awk -F" " '{print $2}' | sed -e 's/\/.*$//')
echo "Local Ip is ${MYIP}"
export MYIP

TXPOWER=0
BRATE=54
MANETDIR=/home/eduardo/devel/argos_real/scripts/MANET/
export MANETDIR
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
echo $DIR
# some globals
EXPERIMENT_SCRIPT=${DIR}/letter_SCRIPT.sh
export EXPERIMENT_SCRIPT

CLICK_SCRIPT=${DIR}/start_click_SCRIPT.sh
export CLICK_SCRIPT
CLICKPRG="/home/root/manet/click/BROADCAST_RNP_PKGclick"
CLICKPRGTOKILL="BROADCAST_RNP_PKGclick"
export CLICKPRG
export CLICKPRGTOKILL

CLICKCONF="/home/root/manet/click/scripts/aligned_broadcast_rnp_linux"
#CLICKCONF="/home/root/manet/click/scripts/aligned_broadcast_rnp_linux"
export CLICKCONF

#TODO parametrize the kill_controller -> gives error
ARGOS_CONTROLLER="footbot_lql_collector"
export ARGOS_CONTROLLER

CTIME=$(date -u +%Y%m%d_%H%M%S)
export CTIME

CLICKLOGFILE="/home/root/eduardo/logs/${CTIME}_click.log"
export CLICKLOGFILE
DO_WIFI=false
DO_SYNC=true
DO_CONTROLLER=true
DO_LOG_CONTROLLER=false
DO_CLICK=false
DO_CHECK_CLICK=false
DO_LOG_CLICK=false
echo "current time ${CTIME}"
checkalive()
{
  PINGCMD="ping -r -n -w 1 -c 1 "
  IPEND=$((${1} + 100))
  ROBOTLOCALIP=10.0.0.${IPEND}
  ${PINGCMD} ${ROBOTLOCALIP} > /dev/null
  if [[ $? != "0" ]]; then
    echo "CHECK FAILED FOR ${1}"
    return 0
  fi
  return 1
}

run_click()
{
  IPEND=$((${1} + 100))
  ROBOTLOCALIP=10.0.0.${IPEND}
  MYCLICKCONF="${CLICKCONF}_n${1}.click"
  ssh root@${ROBOTLOCALIP} \
    "bash -s" -- < ${CLICK_SCRIPT} ${CLICKPRG} ${MYCLICKCONF} ${CLICKLOGFILE} &
  if [[ $? != "0" ]]; then
    echo "CLICK FAILED FOR ${1}"
    return 0
  fi
  return 1
}

log_click()
{
  IPEND=$((${1} + 100))
  ROBOTLOCALIP=10.0.0.${IPEND}
  MYCLICKLOGFILE=/tmp/click_fb$1.log
  echo "logging with nc from ip ${ROBOTLOCALIP} in ${MYCLICKLOGFILE}"
  $( nc ${ROBOTLOCALIP} 12345 > ${MYCLICKLOGFILE} & )
  return 1
}

kill_click()
{
  IPEND=$((${1} + 100))
  ROBOTLOCALIP=10.0.0.${IPEND}
  ssh root@${ROBOTLOCALIP} 'kill -9 $(pidof BROADCAST_RNP_PKGclick)'
  if [[ $? != "0" ]]; then
    echo "KILL CLICK FAILED FOR ${1}"
    return 0
  fi
  return 1
}


kill_controller()
{
  IPEND=$((${1} + 100))
  ROBOTLOCALIP=10.0.0.${IPEND}
  ssh root@${ROBOTLOCALIP} 'kill -9 $(pidof footbot_lql_collector)'
  if [[ $? != "0" ]]; then
    echo "KILL CONTROLLER FAILED FOR ${1}"
    #return 0
  fi
  ssh root@${ROBOTLOCALIP} "pkill tail"
  if [[ $? != "0" ]]; then
    echo "KILL TAIL FAILED FOR ${1}"
    #return 0
  fi
  ssh root@${ROBOTLOCALIP} "pkill nc"
  if [[ $? != "0" ]]; then
    echo "KILL NC FAILED FOR ${1}"
    #return 0
  fi
  ssh root@${ROBOTLOCALIP} "resurrect"
  if [[ $? != "0" ]]; then
    echo "RESURRECT FAILED FOR ${1} - IF IT IS MOVING - CATCH IT!"
    #return 0
  fi

  return 1
}

run_controller()
{
  IPEND=$((${1} + 100))
  ROBOTLOCALIP=10.0.0.${IPEND}
  ssh root@${ROBOTLOCALIP} \
    "bash -s" -- < ${EXPERIMENT_SCRIPT} $1 ${CTIME} &
  if [[ $? != "0" ]]; then
    echo "CONTROLLER FAILED FOR ${1}"
    return 0
  fi
  return 1
}

log_controller()
{
  IPEND=$((${1} + 100))
  ROBOTLOCALIP=10.0.0.${IPEND}
  echo -n | nc ${ROBOTLOCALIP} 4321 &> ${CTIME}_fb${1}.log &
}

check_click()
{
  IPEND=$((${1} + 100))
  ROBOTLOCALIP=10.0.0.${IPEND}
  # check routes
  RVAL=$(ssh root@${ROBOTLOCALIP} 'ip route list | grep -ci wlan1')
  if [[ $? != "0" ]]; then
    echo "check_click failed for ${1} - node down?"
    return 0
  fi
  if [[ $RVAL != "0" ]]; then 
    echo "ERROR: route for wlan1 in $1 - retval: $RVAL"
  fi
  RVAL=$(ssh root@${ROBOTLOCALIP} 'ip route list | grep -ci fake0')
  if [[ $? != "0" ]]; then
    echo "check_click failed for ${1} - node down?"
    return 0
  fi
  if [[ $RVAL != "0" ]]; then 
    echo "ERROR: no route for fake0 in $1 - retval: $RVAL"
  fi
  # check click running
  RVAL=$(ssh root@${ROBOTLOCALIP} 'pidof BROADCAST_RNP_PKGclick')
  if [[ $? != "0" ]]; then
    echo "check_click failed for ${1} - node down?"
    return 0
  fi
  if [[ -z $RVAL ]]; then 
    echo "ERROR: click not running in $1"
    return 0
  fi
  return 1
}
export -f checkalive
export -f run_click
export -f kill_click
export -f log_click
export -f run_controller
export -f kill_controller
export -f log_controller
export -f check_click
for i in ${@:1}
do
  echo "Checking  ${i}"
  checkalive $i
  if [[ $? == "0" ]]; then
    echo "Fatal: Robot $i is not alive!"
    exit 0
  fi
done

echo "All robots OK"

if [[ "$DO_SYNC" = true ]]; then
	bash ${MANETDIR}/SYNC_TIME.sh \
	  ${MYIP} ${@:1}
fi

if [[ "$DO_WIFI" = true ]]; then
bash ${MANETDIR}/SETUP_WIFI_ADHOC.sh \
  ${TXPOWER} 1 ${BRATE} ${@:1}
sleep 2
fi

if [[ "$DO_CLICK" = true ]]; then
  bash ${MANETDIR}/INIT_CLICK.sh \
  ${@:1}
  #some sleep to initialize the wifi
  sleep 2 
  parallel --gnu --jobs 0 run_click ::: ${@:1}
  if [[ "$DO_LOG_CLICK" = true ]]; then
    # sleep one second to allow click to initialize
    sleep 2
    parallel --gnu --jobs 0 log_click ::: ${@:1}
    #
  fi
fi

if [[ "$DO_CONTROLLER" = true ]]; then
  parallel --gnu --jobs 0 run_controller ::: ${@:1}
  #
  if [[ "$DO_LOG_CONTROLLER" = true ]]; then
    sleep 2
    parallel --gnu --jobs 0 log_controller ::: ${@:1}
  fi
fi

# check click
if [[ "$DO_CHECK_CLICK" = true ]]; then
  parallel --gnu --jobs 0 check_click ::: ${@:1}
fi

if [[ "${WAIT_FOR_INPUT}" = true ]]; then
  read -p "Press [Enter] key to finish"
else
  sleep ${EXP_TIME}
fi


jobs -p

if [[ "$DO_CLICK" = true ]]; then
  parallel --gnu --jobs 0 kill_click ::: ${@:1}
  sleep 2
fi

if [[ "$DO_CONTROLLER" = true ]]; then
  parallel --gnu --jobs 0 kill_controller ::: ${@:1}
fi
#echo $(jobs -p)

argos_conf=$( readlink -f $1)
net_scene=$( readlink -f $2)

ns3_conf=/home/eduardo/devel/ns3_pplql/ns-allinone-3.12.1/ns-3.12.1/scratch/swarmanoidIntegration/default.conf

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
echo $DIR

NS3_DIR=/home/eduardo/devel/ns3_pplql/ns-allinone-3.12.1/ns-3.12.1/

function cleanup()
{
  if [ "$(pidof swarmanoidIntegration)" ] 
  then
    echo "ns3 still running ? we kill it!"
    kill -9 $(pidof swarmanoidIntegration)
  fi

  if [ "$(pidof argos)" ]
  then
    echo "argos still running ? don't worry, I kill it!"
    kill -9 $(pidof argos)
  fi

}


trap cleanup INT

if [ "$(pidof swarmanoidIntegration)" ] 
then
  echo "Another instance of ns3 is running PID with $(pidof swarmanoidIntegration) "
    read -p "shall we kill it? " -n 1 -r
    echo    # (optional) move to a new line
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
      killall swarmanoidIntegration
    else
      exit 0
    fi
fi


if [ "$(pidof argos)" ]
then 
  echo "Another instance of argos is running with PID $(pidof argos)"
  read -p "shall we kill it? " -n 1 -r
  echo    # (optional) move to a new line
  if [[ $REPLY =~ ^[Yy]$ ]]
  then
    killall argos
  else
    exit 0
  fi
fi


######### run ns-3 ############
cd ${NS3_DIR}
./waf --run "scratch/swarmanoidIntegration/swarmanoidIntegration \
  ${ns3_conf} RoboNetSim_NS3.dat" &> ~/tmp/ns3_click.out &

######### rnp solve ##########
### must run first because it opens the connection
#cd ~/devel/robot_letter/
#PYTHONPATH=$PYTHONPATH:/home/eduardo/devel/online_rnp/solve/python/ \
#  ./send_letter.py ${net_scene} letters.dat &


sleep 1

######### run argos ##########
cd ~/projects/argos_sim/argos-RoboNetSim/

launch_argos -c ${argos_conf} 

while [ "$(pidof argos)" ]
do
  sleep 1
done

echo "argos done?"
cleanup



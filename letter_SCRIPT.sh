# params <robot_id> <current_time>
ctime=$2
LOGFILE=/home/root/eduardo/logs/${ctime}_footbot_lql_collector.log
# make log dir
mkdir -p eduardo/logs
LD_LIBRARY_PATH=/home/root/ARGoS/lib:/home/root/manet/controllers/ \
  /home/root/manet/controllers/footbot_lql_collector -i lqlcollect \
  -c /home/root/manet/controllers/xml/letters/letters_all.xml &> \
  $LOGFILE &
# send output through netcat
#uncomment to do remote logging with netcat
#tail -f $LOGFILE | \
#  /home/root/manet/netutils/nc -l -p 4321 &


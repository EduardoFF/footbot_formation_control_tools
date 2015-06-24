

USAGE="<footbot id>\ncopies the key to enable ssh without passwd"
if [ "$#" -ne "1" ]
then
    echo -e "${USAGE}"
      exit
fi


FID=$1
FIP=10.0.0.1${1}
#FIP=192.168.201.1${1}
ssh root@${FIP} 'cp ~/.ssh/authorized_keys ~/.ssh/authorized_keys.bak'
cat /home/eduardo/.ssh/id_rsa.pub | ssh root@${FIP} 'cat >> .ssh/authorized_keys'
echo "Done"

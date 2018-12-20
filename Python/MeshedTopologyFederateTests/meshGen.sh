#!/bin/bash

## run as ./meshGen.sh 5 1 1 2 1 5 zmq

federates=$1      #input -- Federate number
messages=$2       #input -- number of federate messages
number_bytes=$3   #input -- number of bytes of the message
connections=$4    #input -- number of connections
timeDelta=$5      #input -- update interval
timeStop=$6       #stop time
coreType=$7       #input -- core type

filepath='log_files/config_runner.json'

#rm -rf test_logs/
#rm -rf test_federates/
#mkdir test_logs
#mkdir test_federates

python Json_create.py $federates $messages $number_bytes $connections $timeDelta $timeStop $coreType &

wait

helics_broker --federates $federates --loglevel 5 > broker.log &

time -p helics run --path $filepath

#for ((i=1;i<=federates;i++))
#do
#python federate.py $number_bytes $timeDelta $timeStop fed_$i.json > test_logs/fed_$i.log &
#done
#
#wait
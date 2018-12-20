#!/bin/bash

# call as ./fedGen.sh 10 2
# first input parameter is number of federates to generate, second is number of subscriptions for each federate.
t=$1
q=$2
if [ -z "$q" ]
then
q=1
fi

if [ "$q" -ge "$t" ]
then
echo "Subscription number greater or equal to publications (insufficient publication targets). Exiting."
exit
fi

rm -rf test_logs/
rm -rf test_federates/
mkdir test_logs
mkdir test_federates

for ((i=1; i<=t;i++))
do
echo "{
 \"name\": \"fed_$i\",
 \"log_level\": 2,
 \"observer\": false,
 \"rollback\": false,
 \"only_update_on_change\": false,
 \"only_transmit_on_change\": false,
 \"source_only\": false,
 \"uninterruptible\": true,
 \"coreType\": \"zmq\",
 \"coreName\": \"\",
 \"coreInit\": \"1\",
 \"maxIterations\": 1,
 \"period\": 1.0,
 \"offset\": 0.0,
 \"timeDelta\": 1.0,
 \"outputDelay\": 0,
 \"inputDelay\": 0,
 \"publications\":[
 {
  \"key\":\"pub\", 
  \"type\":\"double\",
  \"unit\":\"m\",
  \"global\":false,
  \"info\":\"This is a random string containing some info for fed_$i publication\"
 }],
\"subscriptions\":[" > test_federates/fed_$i.json

for ((index=1;index<=q;index++))
do
let r=i+index

if [[ "$r" -gt "$t" ]]
then
#echo "r too large at $r > $t"
let r=i+index-t
fi

echo "
 {
   \"key\":\"fed_$r/pub\", 
   \"type\":\"double\", 
   \"unit\":\"m\",
   \"required\":false,
   \"info\":\"This is a random string containing some info for fed_$i subscription\"
}" >> test_federates/fed_$i.json

if [[ "$index" -ne "$q" ]]
then
echo ",
" >> test_federates/fed_$i.json
fi
done
 echo "]
}" >> test_federates/fed_$i.json
done

#time 
helics_broker -f $t --loglevel 5 > broker.log &
#valgrind --tool=callgrind --callgrind-out-file=broker.out helics_broker -f $t --loglevel 5 &

for ((i=1;i<=t;i++))
do
#valgrind --tool=callgrind --callgrind-out-file=test_logs/fed_$i.out ./valueFed test_federates/fed_$i.json 1 > test_logs/fed_$i.log &
./valueFed test_federates/fed_$i.json 1 > test_logs/fed_$i.log &
done

wait 

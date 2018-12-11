#Created on Mon Nov 20, 2018
#@author: Gayathri krishnamoorthy

import time
import helics as h
import sys
import scipy


number_sender=int(sys.argv[1])
time_stop=float(sys.argv[2])
core_type=str(sys.argv[3])
config_string = sys.argv[4]
print(config_string)

if (core_type==str('IPC')):
    initstring = ("--federates=%s --name=stevebroker" %(number_sender+1))
    core_broker="INTERPROCESS"
    fedinitstring = "--broker=stevebroker --federates=1"
    print('using IPC core')
else:
    initstring = ("--federates=%s --name=mainbroker" %(number_sender+1))
    fedinitstring = "--broker=mainbroker --federates=1"
    core_broker = core_type

helicsversion = h.helicsGetVersion()
#print("ECHOER: Helics version = {}".format(helicsversion))
overall_time=[]
time_start = time.time()
#................................................. Create broker................................. #

print("Creating Broker")
broker = h.helicsCreateBroker(core_broker, "", initstring)
isconnected = h.helicsBrokerIsConnected(broker)
if isconnected == 1:
    print("Broker created and connected")

#...............................................Create Federate..................................

vfed = h.helicsCreateValueFederateFromConfig(config_string)
status = h.helicsFederateRegisterInterfaces(vfed, config_string)
federate_name = h.helicsFederateGetName(vfed)
print(" Federate {} has been registered".format(federate_name))
pubkeys_count = h.helicsFederateGetPublicationCount(vfed)
subkeys_count = h.helicsFederateGetInputCount(vfed)

pubid = {}
subid = {}
for i in range(0,pubkeys_count):
    pubid["m{}".format(i)] = h.helicsFederateGetPublicationByIndex(vfed, i)
for i in range(0,subkeys_count):
    subid["m{}".format(i)] = h.helicsFederateGetInputByIndex(vfed, i)

status = h.helicsFederateEnterExecutingMode(vfed)
#print("ECHOER: Entering execution mode")

#............................................. Main script ..................................#
value = str(0)
currenttime=0.0
time_step_latency=[]

while (currenttime < time_stop):

    currenttime = h.helicsFederateRequestTime(vfed, time_stop)
    #print("ECHOER: Current time is {} ".format(currenttime))
    #print("Request Time = {}".format(time_stop))
    #print("Granted Time = {}".format(currenttime))
    #if currenttime >= time_stop:
        #continue 
    start = time.time()
    for i in range (0, subkeys_count):
        sub = subid["m{}".format(i)]
        isupdated = h.helicsInputIsUpdated(sub)
        if (isupdated == 1):
            last_update_time = h.helicsInputLastUpdateTime(sub)
            value = h.helicsInputGetString(sub)
            #print("Echoer: Last updated at time {}".format(last_update_time))
            #print("ECHOER: Received value = {} at time {}".format(value, currenttime))
            
            #for j in range (0, pubkeys_count):
            pub = pubid["m{}".format(i)]
            status = h.helicsPublicationPublishString(pub, value)
            print("ECHOER: Published value = {} at time {}".format(value, currenttime))
    end = time.time()
    time_step_latency.append(end - start)
       
status = h.helicsFederateFinalize(vfed)

while (h.helicsBrokerIsConnected(broker)):
    time.sleep(0.01)

h.helicsFederateFree(vfed)
h.helicsCloseLibrary()
h.helicsCleanupLibrary()

time_end = time.time()
overall_time.append(time_end - time_start)
print(overall_time)

print("ECHOER: Federate finalized")
print(time_step_latency)


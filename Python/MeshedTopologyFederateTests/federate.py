#Created on Mon Nov 20, 2018
#@author: Gayathri krishnamoorthy

import time
import helics as h
import sys
import scipy

number_bytes=int(sys.argv[1])
update_interval=float(sys.argv[2])
time_stop=float(sys.argv[3])
config_string = str(sys.argv[4])
print(config_string)
##................................................. Create broker................................. #
#for i in range (0, number_sender):
#if (number_sender ==
#print("Creating Broker")
#broker = h.helicsCreateBroker(core_broker, "", initstring)
#isconnected = h.helicsBrokerIsConnected(broker)
#if isconnected == 1:
#    print("Broker created and connected")

#...............................................Create Federate..................................

vfed = h.helicsCreateValueFederateFromConfig(config_string)
status = h.helicsFederateRegisterInterfaces(vfed, config_string)
federate_name = h.helicsFederateGetName(vfed)
print(" Federate {} has been registered".format(federate_name))
pubkeys_count = h.helicsFederateGetPublicationCount(vfed)
print(pubkeys_count)
subkeys_count = h.helicsFederateGetInputCount(vfed)
print(subkeys_count)

pubid = {}
subid = {}
for i in range(0,pubkeys_count):
    pubid["m{}".format(i)] = h.helicsFederateGetPublicationByIndex(vfed, i)
for i in range(0,subkeys_count):
    subid["m{}".format(i)] = h.helicsFederateGetInputByIndex(vfed, i)

status = h.helicsFederateEnterExecutingMode(vfed)
print("Federate: Entering execution mode")

#............................................. Main script ..................................#
value=str()
for i in range (0, number_bytes):
	value=value+'1'
 
t=0.0
currenttime=0.0
time_step_latency=[]

while (t < time_stop):

    t = t + update_interval
    currenttime = h.helicsFederateRequestTime(vfed, t)
    print("Request Time = {}".format(t))
    print("Granted Time = {}".format(currenttime))
        
    start = time.time()                         
    #if (currenttime == t):
    val = str(value)
    for i in range (0, pubkeys_count):
        pub = pubid["m{}".format(i)]
        status = h.helicsPublicationPublishString(pub, val)
        info_pub = h.helicsPublicationGetKey (pub)
        #print("Federate: Published value = {} with key ={} at time {}".format(val, info_pub, currenttime))
        #time.sleep(0.5)   
         
    for i in range (0, subkeys_count):
        sub = subid["m{}".format(i)]
        #print(sub)
        isupdated = h.helicsInputIsUpdated(sub)
        if (isupdated == 1):
            last_update_time = h.helicsInputLastUpdateTime(sub)
            value = h.helicsInputGetString(sub)
            info_sub = h.helicsSubscriptionGetKey (sub) 
            #print("Federate: Last updated at time {}".format(last_update_time))
            #print("Federate: Received value = {} with key = {} at time {}".format(value, info_sub, currenttime))

    end = time.time()                  
    time_step_latency.append(end - start)
       
status = h.helicsFederateFinalize(vfed)

#while (h.helicsBrokerIsConnected(broker)):
#    time.sleep(0.01)

h.helicsFederateFree(vfed)
h.helicsCloseLibrary()
h.helicsCleanupLibrary()

print("Federate finalized")
#print(time_step_latency)

